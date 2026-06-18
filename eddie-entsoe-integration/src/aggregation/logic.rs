//
// logic implementation for energy production data aggregation and emission estimation
//

use std::collections::HashMap;
use std::default;
use std::hash::RandomState;
use chrono::NaiveDateTime;

use crate::entsoe::GlMarketDocument;
use crate::server::api::RequestedTimeSeries;
use super::schema::*;

const UNKNOWN_PSR_TYPE: &str = "unspecified";

fn duration_from_time_strings(start_str: &str, end_str: &str, format_option: Option<&str>) -> u32 {
    
  let date_format = match format_option {
    Some(d) => d,
    None => "%Y-%m-%dT%H:%MZ"
  };

  let duration = match NaiveDateTime::parse_from_str(start_str,date_format) {
    Ok(start) => {
      match NaiveDateTime::parse_from_str(end_str,date_format) {
        Ok(end) => {
          (end - start).num_minutes().abs() as u32
        },
        Err(e) => {
            log::error!("end time \"{}\" error: {}", end_str, e);
            panic!("cannot parse end datetime string")
        }
      }
    }, 
    Err(e) => {
      log::error!("start time \"{}\" error: {}", start_str, e);
      panic!("Cannot parse start datetime string")
    }
  };

  duration
}

// aligning input and output intervals
// TODO: deal with integer division remainders !!
// TODO: deal with input interval augmentation
fn harmonize_intervals(quantity_series: &AggregationSeries<QuantityValue>, from_cnt: u32, to_cnt: u32) -> AggregationSeries<QuantityValue> {

  let mut harmonized_series = AggregationSeries::<QuantityValue>::default();

  let steps = if from_cnt > to_cnt { from_cnt / to_cnt } else { to_cnt / from_cnt };

  let mut inner_step:u32 = 0;
  let mut inner_sum: u32 = 0;

  for quantity in quantity_series {  
    if from_cnt > to_cnt {
      let partial_val = quantity / steps;
      let mut remainder: u32 = quantity % steps;

      log::debug!("harmonize_intervals(series,{from_cnt},{to_cnt}: steps={steps}, val={quantity}, partial_val={partial_val}, remainder={remainder}");

      for _i in 0..steps {
        harmonized_series.push(partial_val + if remainder > 0 { remainder -= 1; 1 } else { 0 });  
      }

    } else if to_cnt < from_cnt {
      if inner_step < steps {
        inner_sum += quantity;
        inner_step += 1;
      } else {
        inner_step = 0;
         harmonized_series.push(inner_sum);
         inner_sum = *quantity;
      }
    } else {
      harmonized_series.push(*quantity);
    }
  }

  harmonized_series
}

// sum by production type over entire time interval
pub fn aggregate_quantities(doc: GlMarketDocument) -> AggregationByType<QuantityValue> {
  let mut production: AggregationByType<QuantityValue> = AggregationByType::default();
  production.unit = ENERGY_UNIT.into();

  production.start_time = doc.time_period_time_interval.start;
  production.end_time = doc.time_period_time_interval.end;

  for time_vector in doc.time_series {
    let psr_type = match time_vector.mkt_psrtype {
      Some(pt) => pt.psr_type,
      None => UNKNOWN_PSR_TYPE.into(), //todo!(),
    };
    
    for point in time_vector.period.point {
      production.aggregate(psr_type.as_str(), point.quantity);
    }
  };

  production
}

// sum by production over time series points
pub fn aggregate_quantity_series(doc: GlMarketDocument, requested_resolution: &str) -> AggregationByType<AggregationSeries<QuantityValue>> {
  let mut series: AggregationByType<AggregationSeries<QuantityValue>> = AggregationByType::default();
  series.unit = ENERGY_UNIT.into();

  series.start_time =  doc.time_period_time_interval.start;
  series.end_time = doc.time_period_time_interval.end;

  for time_vector in doc.time_series {
    let psr_type = match time_vector.mkt_psrtype {
        Some(pt) => pt.psr_type,
        None => UNKNOWN_PSR_TYPE.into(), //todo!(),
    };
    for point in time_vector.period.point {
        series.aggregate(psr_type.as_str(), point.quantity, &time_vector.period.resolution);
    }

    log::debug!("ENTSOE response resolution: {}", &time_vector.period.resolution);
  };

  // sustainable and total calculation here:
  let resolution = series.resolution.unwrap();
  let duration = duration_from_time_strings(&series.start_time, &series.end_time, None);
  let interval_count: u32 = duration / resolution;
  let response_interval = resolution_str_to_interval(requested_resolution);

  // now go through all production types and harmonize intervals
  // could be skipped if intervals are ident
  let mut new_prod_interval = ProductionValues::<AggregationSeries<QuantityValue>>::new();

  for (nam, series) in &series.production {
    let new_series = harmonize_intervals(
      &series, 
      resolution, 
      response_interval);

    new_prod_interval.insert(nam.clone(), new_series);
  }

  series.production = new_prod_interval;
  series.resolution = Some(response_interval);
  let interval_count: u32 = duration / response_interval;

  for _i in 0..interval_count {
    series.sustainable.push(0);
    series.non_sustainable.push(0);
    series.total.push(0);
  }

  series.intervals = Some(interval_count);

  for (name, interval_quantities) in &series.production {
    let mut i: usize = 0;
    let qs_len = &interval_quantities.len();

    for q in interval_quantities {
      if i >= interval_count as usize {
        log::warn!("Interval missmatch received(duration={duration}min, time series entries={qs_len}, expected={interval_count} )");
        break;
      }

      if EmissionCategory::from_production_type(name.as_str()).is_sustainable() {
        series.sustainable[i] += q;
      } else {
        series.non_sustainable[i] += q;
      }

      series.total[i] += q;
      i += 1;
    }
  }

  series
}


fn calculate_interval_totals(agg: &AggregationByType<AggregationSeries<QuantityValue>>, count: u32) -> Vec<QuantityValue> {

  let mut totals = Vec::with_capacity(count as usize);

  for _i in 0..count {
    totals.push(0);
  }

  for (_name, value) in agg.production.clone() {
    let mut i: usize = 0;
    
    for vi in value {
      if i < count as usize {
        totals[i] = &totals[i] + vi;
      } else {
        break;
      }

      i += 1;
    }
  }

  totals
}

// sum by production type over entire time interval
pub fn aggregate_proportion_series(doc: GlMarketDocument) -> AggregationByType<AggregationSeries<ProportionValue>> {
    
  let mut proportions: AggregationByType<AggregationSeries<ProportionValue>> = AggregationByType::default();
  proportions.unit = PROPORTION_UNIT.into();
  let quantities = aggregate_quantity_series(doc, DEFAULT_RESOLUTION);

  proportions.start_time = quantities.start_time.clone();
  proportions.end_time = quantities.end_time.clone();
  proportions.resolution = quantities.resolution;

  let interval_count = quantities.intervals.unwrap();
  log::debug!("calculating for number of intervals: {}", interval_count);

  let interval_totals = &calculate_interval_totals(&quantities, interval_count);
  
  for i in 0..interval_count as usize {
    proportions.sustainable.push(quantities.sustainable[i] as f32 / interval_totals[i] as f32);
    proportions.non_sustainable.push(quantities.non_sustainable[i]  as f32 / interval_totals[i] as f32);
    proportions.total.push(quantities.total[i] as f32 / interval_totals[i] as f32);
  }

  for (name, interval_quantities) in quantities.production {
    let mut prop_series : AggregationSeries<ProportionValue> = AggregationSeries::default();

    let mut i = 0;
    for q in interval_quantities {
      if i < interval_totals.len() {
        prop_series.push(q as f32 / interval_totals[i] as f32);
      } else {
        break;
      }
      i += 1;
    }
    proportions.production.insert(name, prop_series );
  }

  proportions
}

// sum of emissions by production type over entire time interval
pub fn aggregate_emissions(doc: GlMarketDocument) -> AggregationByType<EmissionValues> {

  let quantities =  aggregate_quantities(doc);

  let duration = duration_from_time_strings(&quantities.start_time, &quantities.end_time, None);

  let mut production: ProductionValues<EmissionValues> = ProductionValues::new();

  let mut sustainable = EmissionValues::default();
  let mut non_sustainable = EmissionValues::default();
  let mut total = EmissionValues::default();

  for (name, val) in quantities.production {
    let em_category = EmissionCategory::from_production_type(name.as_str());
    let em_value = em_category.calculate_co2_emission(val, duration);

    production.insert(name.clone(), em_value.clone());

    // sum up sustainable, nonsustainable values
    if em_category.is_sustainable() {
      sustainable = sustainable + em_value.clone();
    } else {
      non_sustainable = non_sustainable + em_value.clone();
    }

    total = total + em_value.clone();
    
    match em_category {
      EmissionCategory::Unknown => {
        log::warn!("unknown emission for: {name} amount {val} {ENERGY_UNIT} assuming arithmetic mean");
      }
      _ => {}
    }
  } 

  AggregationByType::<EmissionValues> {
    start_time             : quantities.start_time,
    end_time               : quantities.end_time,
    unit                   : EMISSION_UNIT.into(),
    resolution             : quantities.resolution,
    intervals              : quantities.intervals,

    production, 

    total,
    sustainable,
    non_sustainable
  }
}

pub fn emission_series_by_total(doc: GlMarketDocument, consumer_values: RequestedTimeSeries) -> RequestedTimeSeries {
  let emission_aggregation = aggregate_emissions(doc);

  let duration = duration_from_time_strings(&consumer_values.start, &consumer_values.end, Some("%Y%m%d%H%M"));

  let hours_between_consumption_points = duration as f32 / consumer_values.consumption.len() as f32 / 60.0;

  let total = emission_aggregation.total.min as f32 * hours_between_consumption_points / 1000.0; // back to kW

  let resolution_minutes = resolution_str_to_interval(&consumer_values.resolution);

  let interval_minutes = (hours_between_consumption_points * 60.0) as u32; 

  if resolution_minutes != interval_minutes {
    log::warn!("consumption resolution value (={resolution_minutes}) does not match number of consumption points (={interval_minutes})");
  } 

  match consumer_values.unit.as_str() {
    "kWh" => {},
    _ => {
      log::warn!("expected unit kWh but received {}", consumer_values.unit);
    }
  }

  let mut consumption = vec![];
  for pt in consumer_values.consumption {
    consumption.push(pt * total);
  }

  log::debug!("calculationg emission by intervals for: duration={duration}, hours per interval={hours_between_consumption_points}");

  RequestedTimeSeries {
    zone: consumer_values.zone,
    start: consumer_values.start,
    end: consumer_values.end,
    unit: EMISSION_UNIT.into(),
    resolution: consumer_values.resolution,
    consumption
  }

}

