use actix_web::{get, HttpResponse, Responder};

use actix_files::NamedFile;
use actix_web::{web, HttpRequest, Result};
use std::path::PathBuf;

use crate::aggregation::*;
use crate::entsoe::send_production_prediction_request;
use crate::server::ProdByTypeAggregation::*;
use crate::entsoe::send_production_by_type_request;
use crate::entsoe::AcknowledgementMarketDocument;
use crate::server::ProductionParams;
use crate::server::FormInputParams;

#[get("/gui/clear")]
async fn clear_entsoe(_req: HttpRequest) -> HttpResponse {
    const CLEAR_TAG: &str = "Waiting for data ...";

    log::debug!("cleared entsoe response field");

    HttpResponse::Ok().body(CLEAR_TAG)
}

pub async fn index(_req: HttpRequest) -> Result<NamedFile> {
    Ok(NamedFile::open("./www/static/index.html".parse::<PathBuf>()?)?)
}

pub async fn gui(_req: HttpRequest) -> Result<NamedFile> {
    Ok(NamedFile::open("./www/static/gui.html".parse::<PathBuf>()?)?)
}

pub async fn fav(_req: HttpRequest) -> Result<NamedFile> {
    Ok(NamedFile::open("./www/static/favicon.ico".parse::<PathBuf>()?)?)
}

fn make_response_html<T: std::fmt::Debug>(aggregate: &AggregationByType<T>) -> String {
    let start = &aggregate.start_time;
    let end = &aggregate.end_time;
    let unit = &aggregate.unit;
    let total = &aggregate.total;
    let sustainable = &aggregate.sustainable;
    let non_sustainable = &aggregate.non_sustainable;
    
    let mut production = String::from("");
        
    for (key, value) in &aggregate.production {
      production.push_str(
          format!("<tr><td>{0}</td><td>:</td><td>{1:?}</td></tr>\n", key, value).as_str());
    } 

    let resolution = match &aggregate.resolution {
      Some(reso) => format!("interval: {} min", reso),
      None => "summed up".into(),
    };

    format!(
      "<b>from: {start} to {end}, {resolution}</b><br/>
        <table style='width:100%'>
          <tr><th style='width:15%'>PRODUCTION</th><th>:</th><th>in [{unit}]</th></tr>
          <tr><td><hr></td><td><hr></td><td><hr></td></tr>
          {production}
          <tr><td><hr></td><td><hr></td><td><hr></td></tr>
          <tr><td>Sustainable</td><td>:</td><td>{sustainable:#?}</td></tr>
          <tr><td>Non-Sustainable</td><td>:</td><td>{non_sustainable:#?}</td></tr>
          <tr><td>TOTAL</td><td>:</td><td>{total:#?}</td></tr>
        </table>
      ")

}

#[get("/gui/form-input")]
pub async fn gui_form_input(req: HttpRequest) -> impl Responder {

  let params = web::Query::<FormInputParams>::from_query(req.query_string());

  match params {
    Ok(p) => {
      log::info!("Got parameters service={}, area={}, start={}, end={}, aggregation={:#?}", p.service, p.zone, p.start, p.end, p.aggregate);

      let mut resp_xml_str = String::new();

      match p.service.as_str() {
        "history" => {
          resp_xml_str = match send_production_by_type_request(p.zone.as_str(), p.start.as_str(), p.end.as_str()).await {
            Ok(xml_str) => xml_str,
            Err(e) => {
              log::error!("{e}");
              return HttpResponse::BadRequest().body(e.to_string())
            }
          };
        },
        "prediction" => {
          resp_xml_str = match send_production_prediction_request(p.zone.as_str(), p.start.as_str(), p.end.as_str()).await {
            Ok(xml_str) => xml_str,
            Err(e) => {
              log::error!("{e}");
              return HttpResponse::BadRequest().body(e.to_string())
            }
          }
        },

        _ => { panic!("unknown service");}
      }

      match serde_xml_rs::from_str(&resp_xml_str) {
        Ok(entsoe_doc) => {
          let resp_json_str = match &p.aggregate {
            None => {
              log::debug!("passing through unchanged entsoe response");
              format!("{:?}",&entsoe_doc)
            },
            Some(agg) => { 
              log::debug!("providing production by generation type aggregation: {agg:#?}");
              match agg {
                Quantity         => make_response_html::<QuantityValue>(&aggregate_quantities(entsoe_doc)),
                Proportion       => make_response_html::<ProportionValue>(&AggregationByType::from_quantity(aggregate_quantities(entsoe_doc))),
                QuantitySeries   => make_response_html::<AggregationSeries<QuantityValue>>(&aggregate_quantity_series(entsoe_doc, DEFAULT_RESOLUTION)),
                ProportionSeries => make_response_html::<AggregationSeries<ProportionValue>>(&aggregate_proportion_series(entsoe_doc)),
                Emission         => make_response_html::<EmissionValues>(&aggregate_emissions(entsoe_doc)),
                EmissionSeries   => "TODO: EmissionSeries not supported!".into(),
              }
            }
          };

          HttpResponse::Ok().body(resp_json_str)
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
