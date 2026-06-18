#![allow(unused)] // FOR DEVELOPMENT ONLY !!!

// order matters here
mod aggregation;
mod config;
mod entsoe;
mod server;

use actix_web::{App, HttpServer};
use actix_web::web;
use actix_web_lab::middleware::CatchPanic;

use crate::config::SERVER_CONFIG;
use crate::server::gui::*;

#[tokio::main]
pub async fn main() -> std::io::Result<()> {
    let version = env!("CARGO_PKG_VERSION");
    let server_name = env!("CARGO_PKG_NAME");
    let config = &SERVER_CONFIG;

    std::env::set_var("RUST_LOG", &config.log_level);

    env_logger::init();

    let url = config.url.clone();
    let port = config.port;

    log::info!("Starting {server_name} server ver({version}) at {url}:{port}");
    log::info!("Configuration parameters:\n{}", config.as_str());

    HttpServer::new(move || {
        App::new()
            .service(clear_entsoe)
            .service(server::api::energy_mix_series_method)
            .service(server::api::emission_series_method)
            .service(server::api::production_by_type_method)
            .service(server::api::production_prediction_method)
            .service(server::gui::gui_form_input)
            .route("/", web::get().to(index))
            .route("/gui", web::get().to(gui))
            .route("/favicon.ico", web::get().to(fav))
            .wrap(CatchPanic::default())
    })
    .bind((url, port))?
    .run()
    .await
}
