mod schema;
mod client;

pub use schema::{GlMarketDocument, AcknowledgementMarketDocument};
pub use client::send_production_by_type_request;
pub use client::send_production_prediction_request;
//pub use client::cached_production_by_type_request;