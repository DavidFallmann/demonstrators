use serde::{Deserialize, Serialize};


#[derive(Debug, Serialize, Deserialize)]
pub struct GlMarketDocument {
    //pub xmlns: String,
    #[serde(rename = "$text")]
    pub text: Option<String>,
    #[serde(rename = "mRID")]
    pub m_rid: String,
    #[serde(rename = "revisionNumber")]
    pub revision_number: String,
    #[serde(rename = "type")]
    pub gl_market_document_type: String,
    #[serde(rename = "process.processType")]
    pub process_process_type: String,
    #[serde(rename = "sender_MarketParticipant.mRID")]
    pub sender_market_participant_m_rid: SenderMarketParticipantMRid,
    #[serde(rename = "sender_MarketParticipant.marketRole.type")]
    pub sender_market_participant_market_role_type: String,
    #[serde(rename = "receiver_MarketParticipant.mRID")]
    pub receiver_market_participant_m_rid: ReceiverMarketParticipantMRid,
    #[serde(rename = "receiver_MarketParticipant.marketRole.type")]
    pub receiver_market_participant_market_role_type: String,
    #[serde(rename = "createdDateTime")]
    pub created_date_time: String,
    #[serde(rename = "time_Period.timeInterval")]
    pub time_period_time_interval: TimePeriodTimeInterval,
    #[serde(rename = "TimeSeries")]
    pub time_series: Vec<TimeSeries>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct SenderMarketParticipantMRid {
    #[serde(rename = "codingScheme")]
    pub coding_scheme: String,
    #[serde(rename = "$text")]
    pub text: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ReceiverMarketParticipantMRid {
    #[serde(rename = "codingScheme")]
    pub coding_scheme: String,
    #[serde(rename = "$text")]
    pub text: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct TimePeriodTimeInterval {
    #[serde(rename = "$text")]
    pub text: Option<String>,
    pub start: String,
    pub end: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct TimeSeries {
    #[serde(rename = "$text")]
    pub text: Option<String>,
    #[serde(rename = "inBiddingZone_Domain.mRID")]
    pub in_bidding_zone_domain_m_rid: Option<InBiddingZoneDomainMRid>,
    #[serde(rename = "mRID")]
    pub m_rid: String,
    #[serde(rename = "businessType")]
    pub business_type: String,
    #[serde(rename = "objectAggregation")]
    pub object_aggregation: String,
    #[serde(rename = "quantity_Measure_Unit.name")]
    pub quantity_measure_unit_name: String,
    #[serde(rename = "curveType")]
    pub curve_type: String,
    #[serde(rename = "MktPSRType")]
    pub mkt_psrtype: Option<MktPsrtype>,
    #[serde(rename = "Period")]
    pub period: Period,
    #[serde(rename = "outBiddingZone_Domain.mRID")]
    pub out_bidding_zone_domain_m_rid: Option<OutBiddingZoneDomainMRid>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct InBiddingZoneDomainMRid {
    #[serde(rename = "codingScheme")]
    pub coding_scheme: String,
    #[serde(rename = "$text")]
    pub text: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct MktPsrtype {
    #[serde(rename = "$text")]
    pub text: Option<String>,
    #[serde(rename = "psrType")]
    pub psr_type: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct Period {
    #[serde(rename = "$text")]
    pub text: Option<String>,
    #[serde(rename = "timeInterval")]
    pub time_interval: TimeInterval,
    pub resolution: String,
    #[serde(rename = "Point")]
    pub point: Vec<Point>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct TimeInterval {
    #[serde(rename = "$text")]
    pub text: Option<String>,
    pub start: String,
    pub end: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct Point {
    #[serde(rename = "$text")]
    pub text: Option<String>,
    pub position: String,
    pub quantity: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct OutBiddingZoneDomainMRid {
    #[serde(rename = "codingScheme")]
    pub coding_scheme: String,
    #[serde(rename = "$text")]
    pub text: Option<String>,
}

// --- ERROR responses 

#[derive(Debug, Serialize, Deserialize)]
pub struct AcknowledgementMarketDocument {
    //pub xmlns: String,
    #[serde(rename = "$text")]
    pub text: Option<String>,
    #[serde(rename = "mRID")]
    pub m_rid: String,
    #[serde(rename = "createdDateTime")]
    pub created_date_time: String,
    #[serde(rename = "sender_MarketParticipant.mRID")]
    pub sender_market_participant_m_rid: SenderMarketParticipantMRid,
    #[serde(rename = "sender_MarketParticipant.marketRole.type")]
    pub sender_market_participant_market_role_type: String,
    #[serde(rename = "receiver_MarketParticipant.mRID")]
    pub receiver_market_participant_m_rid: ReceiverMarketParticipantMRid,
    #[serde(rename = "receiver_MarketParticipant.marketRole.type")]
    pub receiver_market_participant_market_role_type: String,
    #[serde(rename = "received_MarketDocument.createdDateTime")]
    pub received_market_document_created_date_time: Option<String>,
    #[serde(rename = "Reason")]
    pub reason: Reason,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct Reason {
    #[serde(rename = "$text")]
    pub text_content: Option<String>,
    pub code: String,
    pub text: String,
}
