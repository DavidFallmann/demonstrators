use actix_web::{
    get, post, http::header::ContentType, HttpResponse, Responder,
    HttpRequest, Result, web
};

use serde::{Deserialize, Serialize};
use serde_json::Error;

use crate::aggregation::*;

use crate::entsoe:: { 
  AcknowledgementMarketDocument, GlMarketDocument,
  send_production_by_type_request, 
  send_production_prediction_request
};

use crate::server::ProdByTypeAggregation::*;
use crate::server::ProductionParams;

use super::ProdByTypeAggregation;

#[derive(Debug, Deserialize, Serialize)]
pub struct RequestedTimeSeries {
    pub zone : String,
    pub start: String,
    pub end:   String,
    pub resolution: String,
    pub unit: String,
    pub consumption: Vec<f32>
}

fn make_response_json(doc : GlMarketDocument, aggregate: &Option<ProdByTypeAggregation>, resolution: &str) -> Result<String, Error> {
  match aggregate {
    
    None => {
      log::debug!("passed through production by generation type");
      serde_json::to_string(&doc)
    },

    Some(agg) => { 
      log::debug!("providing production by generation type aggregation: {:#?}", &agg);
      match agg {
        Quantity         => serde_json::to_string(&aggregate_quantities(doc)),
        Proportion       => serde_json::to_string(&AggregationByType::from_quantity(aggregate_quantities(doc))),
        QuantitySeries   => serde_json::to_string(&aggregate_quantity_series(doc, &resolution)),
        ProportionSeries => serde_json::to_string(&aggregate_proportion_series(doc)),
        Emission         => serde_json::to_string(&aggregate_emissions(doc)),
        EmissionSeries   => Ok(String::from("")),
      }
    }
  }
}

#[get("/api/production-by-type")]
pub async fn production_by_type_method(req: HttpRequest) -> impl Responder {

  let params = web::Query::<ProductionParams>::from_query(req.query_string());

  match params {
    Ok(p) => {
      log::info!("Got parameters zone={}, start={}, end={}, aggregation={:#?}", p.zone, p.start, p.end, p.aggregate);

      let resolution = match p.resolution { Some(ref r) => r, None => DEFAULT_RESOLUTION };

      // call ENTSOE API
      let resp_xml_str = match send_production_by_type_request(p.zone.as_str(), p.start.as_str(), p.end.as_str()).await {
        Ok(xml_str) => xml_str,

        Err(e) => {
          log::error!("{e}");
          return HttpResponse::BadRequest().body(e.to_string())
        }
      };

      match serde_xml_rs::from_str(&resp_xml_str) {
        Ok(doc) => {
          let resp_json_str = make_response_json(doc, &p.aggregate, resolution).unwrap();
          HttpResponse::Ok().insert_header(ContentType::json()).body(resp_json_str)
        },

        Err(e) => {
          log::error!("{e}, ENTSOE info: {resp_xml_str}");

          let err_resp_rs: AcknowledgementMarketDocument = serde_xml_rs::from_str(&resp_xml_str).unwrap();
          HttpResponse::BadRequest().body(err_resp_rs.reason.text)
        }
      }
    },

    Err(e) => {
        log::error!("Request URL problem: {e}");
        HttpResponse::BadRequest().body(e.to_string())
    }
  }
}


#[get("/api/production-prediction")]
pub async fn production_prediction_method(req: HttpRequest) -> impl Responder {

  let params = web::Query::<ProductionParams>::from_query(req.query_string());
  
  let resolution = String::from(DEFAULT_RESOLUTION);

  match params {
    Ok(p) => {
      log::info!("Got parameters zone={}, start={}, end={}", p.zone, p.start, p.end);

      // call ENTSOE API
      let resp_xml_str = send_production_prediction_request(p.zone.as_str(), p.start.as_str(), p.end.as_str()).await.unwrap();
      log::debug!("received ENTSOE prediction response");

      let resp_rs: Result<GlMarketDocument, _> = serde_xml_rs::from_str(&resp_xml_str);

      match resp_rs {
        Ok(doc) => {
          let resp_json_str = make_response_json(doc, &p.aggregate, resolution.as_str()).unwrap();
          //let mut resp_json_str = resp_xml_str;
          HttpResponse::Ok().insert_header(ContentType::json()).body(resp_json_str)
        },

        Err(e) => {
          log::error!("Request problem {e}, ENTSOE info: {resp_xml_str}");
          HttpResponse::BadRequest().body(format!("{e:#?}"))
        }
      }
    },

    Err(e) => {
        log::error!("Request URL problem: {e}");
        HttpResponse::BadRequest().body(e.to_string())
    }
  }
}


// --- POST requests

#[post("/api/energy-mix-series")]
pub async fn energy_mix_series_method(time_period: String) -> HttpResponse {
  let req: RequestedTimeSeries = serde_json::from_str(&time_period).unwrap();
  log::debug!("got request energy-mix-series: {:#?}", req);

  let zone = req.zone.as_str();
  let start = req.start.as_str();
  let end = req.end.as_str();

  log::info!("Got energy-mix-parameters zone={zone}, start={start}, end={end}");

  // call ENTSOE API
  let resp_xml_str = match send_production_by_type_request(zone, start, end).await {
    Ok(xml_str) => xml_str,

    Err(e) => {
      log::error!("{e}");
      return HttpResponse::BadRequest().body(e.to_string())
    }
  };

  match serde_xml_rs::from_str::<GlMarketDocument>(&resp_xml_str) {
      Ok(_r) =>
        HttpResponse::Ok().insert_header(ContentType::json()).body(serde_json::to_string(&req).unwrap()),
      Err(e) => 
        HttpResponse::BadRequest().body(format!("{{ \"error\":\"{e:#?}\" }}"))
  }
}

#[post("/api/emission-series")]
pub async fn emission_series_method(time_period: String) -> HttpResponse {
  let req: RequestedTimeSeries = serde_json::from_str(&time_period).unwrap();
  log::info!("got request emission-series: {:#?}", req);

  let zone = req.zone.as_str();
  let start = req.start.as_str();
  let end = req.end.as_str();

  log::info!("Got emission-series parameters:\n{:#?}", req);
  
  // call ENTSOE API
  let resp_xml_str = match send_production_by_type_request(zone, start, end).await {
    Ok(xml_str) => xml_str,

    Err(e) => {
      log::error!("{e}");
      return HttpResponse::BadRequest().body(e.to_string())
    }
  };

  match serde_xml_rs::from_str(&resp_xml_str) {
      Ok(r) => {
        let es = emission_series_by_total(r, req);
        let res_js = serde_json::to_string(&es).unwrap();
        HttpResponse::Ok().insert_header(ContentType::json()).body(res_js) 
      },
      Err(e) => 
        HttpResponse::BadRequest().body(format!("{:#?}", e))
  }
}