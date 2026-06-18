pub mod api;
pub mod gui;

use serde::Deserialize;

#[derive(Debug, Deserialize)]
pub enum ProdByTypeAggregation {
    Quantity,
    Proportion,
    Emission,
    QuantitySeries,
    ProportionSeries,
    EmissionSeries
}

#[derive(Debug, Deserialize)]
pub struct ProductionParams {
    pub zone: String,
    pub start: String,
    pub end: String,
    pub resolution: Option<String>,
    pub aggregate: Option<ProdByTypeAggregation>
}

#[derive(Debug, Deserialize)]
pub struct FormInputParams {
    pub zone: String,
    pub start: String,
    pub end: String,
    pub service: String,
    pub resolution: Option<String>,
    pub aggregate: Option<ProdByTypeAggregation>
}


