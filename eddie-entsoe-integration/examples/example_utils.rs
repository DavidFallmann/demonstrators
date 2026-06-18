#![allow(unused)] // FOR DEVELOPMENT ONLY !!!

use std::collections::HashMap;

use serde::{Deserialize, Serialize};
use reqwest::Client;
use serde_json::Value;

const EMISSION_REQUEST_URL: &str = "http://localhost:8000/api/emission-series";
const EMIX_REQUEST_URL: &str = "http://localhost:8000/api/energy-mix-series";

#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct RequestedTimeSeries {
    pub zone : String,
    pub start: String,
    pub end:   String,
    pub unit: String,
    pub resolution: String,
    pub consumption: Vec<f32>
}

async fn post_query(client: &Client, url: &str, consumption_series: String) -> RequestedTimeSeries {
    
    client
        .post(url)
        .body(consumption_series)
        .send()
        .await
        .expect("failed to get response")
        .json::<RequestedTimeSeries>()
        .await
        .expect("failed to get payload")
}


pub async fn query_emission(client: &Client, consumption_series: String) -> RequestedTimeSeries {  
    post_query(client, EMISSION_REQUEST_URL, consumption_series).await
}

pub async fn query_energy_mix(client: &Client, consumption_series: String) -> RequestedTimeSeries {  
    post_query(client, EMIX_REQUEST_URL, consumption_series).await
}

pub async fn query_production_prediction(client: &Client, start: &str, end: &str, zone: &str, aggregate: &str) -> HashMap<String, Value> { // RequestedTimeSeries {
    let url = format!("http://localhost:8000/api/production-prediction?start={start}&end={end}&zone={zone}&aggregate={aggregate}");
   
    let json_str = client
    .get(url)
    .send()
    .await
    .expect("failed to get response")
    //.json::<RequestedTimeSeries>()
    .text()
    .await
    .expect("failed to get payload");

    let res_map: HashMap<String, Value> = serde_json::from_str(json_str.as_str()).unwrap();

    res_map

}

#[allow(dead_code)]
fn main() {
    println!("This is not an example!");
}
