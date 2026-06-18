use crate::config::SERVER_CONFIG;
use reqwest;

// for experimental function caching
//use cached::proc_macro::cached;
//use std::io::Error;

struct EntsoeRequest<'a> {
    document_type: &'a str,
    process_type: &'a str,
    in_domain: &'a str,
    period_start: &'a str,
    period_end: &'a str
}

impl EntsoeRequest<'_> {
    fn make_request_url(self, addr: &str, security_token: &str) -> String {
        let dtype = self.document_type;
        let ptype  = self.process_type;
        let domain = self.in_domain;
        let start  = self.period_start; 
        let end    = self.period_end;
        
        format!("{addr}?documentType={dtype}&processType={ptype}&in_Domain={domain}&periodStart={start}&periodEnd={end}&securityToken={security_token}") 
    }

    fn map_country_code(code: &str) -> &str {
        match code {
            "EU" => "10YEU-CONT-SYNC0",
            "AT" => "10YAT-APG------L",
            "DE" => "10Y1001A1001A83F",
            "FR" => "10YFR-RTE------C",
            "BE" => "10YBE----------2",
            "DK" => "10Y1001A1001A65H",
            "UK" => "10Y1001A1001A92E",
            "HU" => "10YHU-MAVIR----U",
            "TR" => "10YTR-TEIAS----W",
            "IS" => "IS",
            "SE" => "10YSE-1--------K",
            "NO" => "10YNO-0--------C",
            "PL" => "10YPL-AREA-----S",
            "IT" => "10YIT-GRTN-----B",
            "ES" => "10YES-REE------0",
            _ => code,
        }
    }
}


pub async fn send_production_by_type_request(area: &str, start: &str, end: &str) -> Result<String, reqwest::Error> {

    let prod_gen = EntsoeRequest {

        document_type : "A75",
        process_type  : "A16",
        in_domain     : EntsoeRequest::map_country_code(area), // "10YAT-APG------L",
        period_start  : start,                                 // "202407172200",
        period_end    : end,                                   // "202407182200",
    };

    reqwest::get(prod_gen.make_request_url(&SERVER_CONFIG.entsoe_api_url, &SERVER_CONFIG.security_token))
        .await?
        .text()
        .await
}

pub async fn send_production_prediction_request(zone: &str, start: &str, end: &str) -> Result<String, reqwest::Error> {

    let prod_gen = EntsoeRequest {

        document_type : "A71",
        process_type  : "A01",
        in_domain     : EntsoeRequest::map_country_code(zone), // "10YAT-APG------L",
        period_start  : start,                                 // "202407172200",
        period_end    : end,                                   // "202407182200",
    };

    reqwest::get(prod_gen.make_request_url(&SERVER_CONFIG.entsoe_api_url, &SERVER_CONFIG.security_token))
        .await?
        .text()
        .await
}
