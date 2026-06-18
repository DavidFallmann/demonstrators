use lazy_static::lazy_static;
use serde::Deserialize;
use std::fs::{self};

pub const CONFIG_FILE_NAME: &str = "config.json";

lazy_static! {
    pub static ref SERVER_CONFIG: ServerConfig = ServerConfig::read_from_file(CONFIG_FILE_NAME.into());
}

#[derive(Debug, Deserialize, Default)]
pub struct ServerConfig {
    #[serde(rename = "description")]
    pub _description: Option<String>,

    pub url:  String,
    pub port: u16,

    #[serde(rename = "entsoe-api-url")]
    pub entsoe_api_url: String,

    #[serde(rename = "security-token")]
    pub security_token: String,

    #[serde(rename = "log-level")]
    pub log_level: String
}


impl ServerConfig {

    pub fn read_from_file(fname: &str) -> ServerConfig {

        let config_str = fs::read_to_string(fname);

        match config_str {
            Ok(c) => {
                match serde_json::from_str(c.as_str()) {
                    Ok(conf) => conf,
                    Err(e) => panic!("Syntax error in configuration file '{fname}': {e}")
                }
            },

            Err(_e) => ServerConfig {
                _description: Some("fallback config hardcoded".into()),
                url: "0.0.0.0".into(),
                port: 8000,
                entsoe_api_url: "https://web-api.tp.entsoe.eu/api".into(),
                security_token: "INSERT_SECURITY_TOKEN".into(),

                log_level: "DEBUG".into()
            }
        }
        
    }

    pub fn as_str(&self) -> String {
        format!("{:#?}", &self)
    }
}