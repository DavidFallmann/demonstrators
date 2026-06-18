
mod example_utils;
use crate::example_utils::query_emission;


#[tokio::main]
async fn main() -> std::io::Result<()> {

    std::env::set_var("RUST_LOG", "DEBUG");

    env_logger::init();
    log::info!("energy-mix series example");
    
    let client = reqwest::Client::new();
    
    let res = query_emission(&client, TIME_SERIES_01.into()).await;
    log::info!(" TIME_SERIES_01] got response: {:#?}", &res);

    let res = query_emission(&client, TIME_SERIES_REAL_LONG.into()).await;
    log::info!("[TIME_SERIES_REAL_LONG] got response: {:#?}", &res);

    let res = query_emission(&client, TIME_SERIES_REAL_SHORT.into()).await;
    log::info!("[TIME_SERIES_REAL_SHORT] got response: {:#?}", &res);

    Ok(())
}

const TIME_SERIES_01: &str = r#"
{
    "zone": "AT",
    "start": "202407231200",
    "end":   "202407231300",
    "unit": "kWh",
    "resolution": "PT15M",
    "consumption": [1,2,-3,-4]
}
"#;

#[allow(unused)] 
const TIME_SERIES_02: &str = r#"
{
    "zone": "AT",
    "start": "202407231200",
    "end":   "202407231400",
    "unit": "kWh",
    "resolution": "PT15M",
    "consumption": [1,2,3,4,5,6,7,8]
}
"#;

#[allow(unused)]
const TIME_SERIES_03: &str = r#"
{
    "zone": "FR",
    "start": "202407231200",
    "end":   "202407231400",
    "unit": "kWh",
    "resolution": "PT15M",
    "consumption": [1,2,3,4]
}
"#;


const TIME_SERIES_REAL_LONG: &str = r#"
{ 
    "zone": "AT",
    "start": "202408192200",
    "end": "202408202200",
    "unit": "kWh",
    "resolution": "PT15M",
    "consumption": [0.441, 0.444, 0.104, 0.088, 0.081, 0.079, 0.084, 0.08, 0.083, 0.08, 0.072, 0.072, 0.083, 0.094, 0.074, 0.086, 0.065, 0.076, 0.076, 0.091, 0.08, 0.097, 0.083, 0.088, 0.089, 0.106, 0.127, 0.103, 0.014, 0.0, 0.0, 0.0, 0.003, 0.022, 0.014, 0.003, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.063, 0.028, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.11, 0.026, 0.0, 0.0, 0.098, 0.0, 0.012, 0.228, 0.461, 0.095, 0.24, 0.161, 0.445, 0.853, 0.604, 0.625, 0.648, 0.313, 0.463, 0.567, 0.21, 0.185, 0.127, 0.156, 0.101, 0.168, 0.116, 0.147] }
"#;

const TIME_SERIES_REAL_SHORT: &str = r#"
{ 
    "zone": "AT",
    "start": "202408192200",
    "end": "202408192300",
    "unit": "mWh", 
    "resolution": "PT15M",
    "consumption": [0.441, 0.444, 0.104, 0.088] }
"#;
