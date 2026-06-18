
mod example_utils;
use crate::example_utils::query_production_prediction;


#[tokio::main]
async fn main() -> std::io::Result<()> {
    std::env::set_var("RUST_LOG", "DEBUG");
    env_logger::init();
    log::info!("production prediction series example");

    let client = reqwest::Client::new();
    let start = "202411101200";
    let end = "202411102300";
    let zone = "AT";

    let res = query_production_prediction(&client, start, end, zone, "QuantitySeries").await;
    log::info!("[QuantitySeries] got response: {:#?}", &res);

    let res = query_production_prediction(&client, start, end, zone, "ProportionSeries").await;
    log::info!("[ProportionSeries] got response: {:#?}", &res);

    let res = query_production_prediction(&client, start, end, zone, "Emission").await;
    log::info!("[Emission] got response: {:#?}", &res);

    let res = query_production_prediction(&client, start, end, zone, "Proportion").await;
    log::info!("[Proportion] got response: {:#?}", &res);

    let res = query_production_prediction(&client, start, end, zone, "Quantity").await;
    log::info!("[Quantity] got response: {:#?}", &res);
    

    Ok(())
}
