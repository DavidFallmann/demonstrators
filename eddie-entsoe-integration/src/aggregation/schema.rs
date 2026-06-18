
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

use std::ops;


pub type QuantityValue = u32;
pub type ProportionValue = f32;
pub type AggregationSeries<T> = Vec<T>;
pub type ProductionValues<T> = HashMap<String, T>;


pub const EMISSION_UNIT: &str = "kgCO2eq";
pub const ENERGY_UNIT: &str = "mW";       // entsoe MAW refers to mW
pub const PROPORTION_UNIT: &str = "ratio";

pub const DEFAULT_RESOLUTION: &str = "PT15M";

// --- emission datamodell

// data structures and functions for emission data calculation

// lifecycle emission data number taken from the IPCC (2014) Fifth Assessment Report 
// Appendix III: Technology-specific Cost and Performance Parameters
// (see: https://www.ipcc.ch/site/assets/uploads/2018/02/ipcc_wg3_ar5_annex-iii.pdf#page=7)
// values in:  (gCO2eq / kW/h)


#[derive(Default, Serialize, Clone, Debug)]
pub struct EmissionValues {
    pub min: f64,
    pub medium: f64,
    pub max: f64
}

impl ops::Add<EmissionValues> for EmissionValues {
    type Output = EmissionValues;
    fn add(self, rhs: Self) -> EmissionValues {
        EmissionValues { 
            min: self.min + rhs.min,
            medium: self.medium + rhs.medium,
            max: self.max + rhs.max 
        }
    }
}

#[allow(unused)] 
pub enum EmissionCategory {
    Coal,
    Gas,
    BiomassCofiring,
    BiomassDedicated,
    Geothermal,
    Hydropower,
    Nuclear,
    SolarConcentrated,
    SolarPvRooftop,
    SolarPvUtility,
    WindOnshore,
    WindOffshore,
    Ocean,

    OilGuess,
    SolarGeneric,
    Unknown
}

impl EmissionCategory {
    pub fn value(&self) -> EmissionValues {
        match *self {
            Self::Coal              => EmissionValues { min: 740.0, medium: 820.0, max: 910.0 },
            Self::Gas               => EmissionValues { min: 410.0, medium: 490.0, max: 650.0 },
            Self::BiomassCofiring   => EmissionValues { min: 620.0, medium: 740.0, max: 890.0 },
            Self::BiomassDedicated  => EmissionValues { min: 130.0, medium: 230.0, max: 420.0 },
            Self::Geothermal        => EmissionValues { min:   6.0, medium:  38.0, max:  79.0 },
            Self::Hydropower        => EmissionValues { min:   1.0, medium:  24.0, max:2200.0 }, // can max value be true here?
            Self::Nuclear           => EmissionValues { min:   3.7, medium:  12.0, max: 110.0 },
            Self::SolarConcentrated => EmissionValues { min:   8.8, medium:  27.0, max:  63.0 },
            Self::SolarPvRooftop    => EmissionValues { min:  26.0, medium:  41.0, max:  60.0 },
            Self::SolarPvUtility    => EmissionValues { min:  18.0, medium:  48.0, max: 180.0 },
            Self::WindOnshore       => EmissionValues { min:   7.0, medium:  11.0, max:  56.0 },
            Self::WindOffshore      => EmissionValues { min:   8.0, medium:  12.0, max:  35.0 },
            Self::Ocean             => EmissionValues { min:   5.6, medium:  17.0, max:  28.0 },
            
            Self::OilGuess          => Self::Coal.value(),
            Self::SolarGeneric      => Self::SolarPvRooftop.value(),
            Self::Unknown => EmissionValues { min:   183.3, medium:  224.7, max:  443.4 }, // arithmetic mean value of all known emissions
        }
    }

    pub fn is_sustainable(&self) -> bool {
        match self {
            Self::Geothermal | Self::Hydropower |
            Self:: SolarGeneric | Self::SolarConcentrated | Self::SolarPvRooftop | Self::SolarPvUtility |
            Self::WindOffshore | Self::WindOnshore | Self::Ocean
              => { true }
            _ => { false }
        }
    }

    // calculating CO2eq emission:
    //   m = 1.000.000, k = 1.000, h => 1 hour = 60 min
    //   emission * [gCO2eq/kW/h] * energy * [mW] / (duration * [h]) 
    //   emission * energy * [gCO2eq/kW/h] * [mW] / (duration * [h])
    //   emission * energy * [gCO2eq/kW/h * mW * 1/h] / duration
    //   emission * energy * [gCO2eq/(kW*1/h) * mW * 1/h] / duration
    //   emission * energy * [gCO2eq/kW * mW] / duration
    //   emission * energy * [(gCO2eq * mW)/kW] / duration
    //   emission * energy * [gCO2eq * m/k] / duration
    //   emission * energy * [gCO2eq * k] / duration
    //   emission * energy / duration * [kgCO2eq]
    // 
    pub fn calculate_co2_emission(&self, energy_in_mw: u32, duration_in_min: u32) -> EmissionValues {
        const HOUR: f64 = 60.0;
    
        let cat_val = self.value();

        let duration_in_h = duration_in_min as f64 / HOUR;
        let production_per_h = energy_in_mw as f64 / duration_in_h ;
        
        EmissionValues {
            min:    cat_val.min * production_per_h,
            medium: cat_val.medium * production_per_h,
            max:    cat_val.max * production_per_h,
        }
    }

    pub fn from_production_type(name: &str) -> EmissionCategory {
        match name {
            "biomass" =>  Self::BiomassCofiring,
            "fossil_brown" =>  Self::Coal, 
            "fossil_coal_derived_gas" =>  Self::Coal, 
            "fossil_gas" =>  Self::Gas,
            "fossil_hard_coal" =>  Self::Coal,
            "fossil_oil" =>  Self::OilGuess,
            "fossil_oil_shale" =>  Self::OilGuess,
            "fossil_peat" =>  Self::OilGuess, 
            "geothermal" =>  Self::Geothermal,
            "hydro_pumped_storage" =>  Self::Hydropower, 
            "hydro_run_of" =>  Self::Hydropower, 
            "hydro_reservoir" =>  Self::Hydropower, 
            "marine" =>  Self::Ocean,
            "nuclear" =>  Self::Nuclear, 
            "other_renewable" =>  Self::Unknown, 
            "solar" =>  Self::SolarGeneric, 
            "waste" =>  Self::Unknown, 
            "wind_offshore" =>  Self::WindOffshore, 
            "wind_onshore" =>  Self::WindOnshore, 
            "other_any" =>  Self::Unknown,
    
            _ => Self::Unknown
        }
    }
}


// --- aggregation data modell

#[derive(Debug, Serialize, Deserialize, Default)]
pub struct AggregationByType<T> {
    pub start_time: String, 
    pub end_time: String,
    pub unit: String,
    pub resolution: Option<u32>,
    pub intervals: Option<u32>,

    pub production: ProductionValues<T>,

    pub total : T,
    pub sustainable : T,
    pub non_sustainable : T,
}

impl AggregationByType<QuantityValue> {

    pub fn aggregate(&mut self, psrt: &str, quantity: String) {
        let q_u32 = quantity.parse::<QuantityValue>().unwrap();
        self.total += q_u32;
        
        self.production.entry(prod_name_from_psrt(psrt).into())
                .and_modify(|prod| *prod += q_u32)
                .or_insert(q_u32);

    }
}

impl AggregationByType<ProportionValue> {
    pub fn from_quantity(q: AggregationByType<QuantityValue>) -> Self {
        let total = q.total as f32;

        let mut hmap: ProductionValues<ProportionValue> = ProductionValues::new();

        for (name, quantity) in q.production {
            hmap.insert(name, quantity as f32 / total);
        }

        let mut sustainable: ProportionValue = 0.0;
        let mut non_sustainable: ProportionValue = 0.0;
        let mut total: ProportionValue = 0.0;

        for (name, value) in &hmap {
            total += value;
            
            if EmissionCategory::from_production_type(name).is_sustainable() {
                sustainable += value;
            } else {
                non_sustainable += value;
            }
        }

        Self {
            start_time             : q.start_time,
            end_time               : q.end_time,
            unit                   : PROPORTION_UNIT.into(),
            resolution             : q.resolution,
            intervals              : q.intervals,

            production: hmap,

            total : total as ProportionValue,
            sustainable : sustainable as ProportionValue * 0.4 , // TODO: real value calculation
            non_sustainable: non_sustainable as ProportionValue * 0.6,
        }
    }
}

impl AggregationByType<AggregationSeries<QuantityValue>> {
    
    // sum by production type over entire time interval
    // TODO: Verify common time interval (start, end, resolution) for all timeseries accumulated
    pub fn aggregate(&mut self, psrt: &str, quantity: String, resolution_str: &str) {
        let q_u32: QuantityValue = quantity.parse().unwrap();
        
        self.resolution = Some(resolution_str_to_interval(resolution_str.into()));

        //self.total += q_u32;
        self.total = vec![]; //CHANGEME: get real totals (should be all 1.0 anyways)

        let name = prod_name_from_psrt(psrt);

        
        let mut series: AggregationSeries<QuantityValue> = match self.production.get::<str>(name) {
            Some(v) => v.clone(),
            None => AggregationSeries::default()
        };

        series.push(q_u32);

        self.production.insert(name.into(), series);

    }
}


// util functions for mapping

pub fn resolution_str_to_interval(resolution: &str) -> u32 {
    match resolution {
        "PT60M" => 60,
        "PT30M" => 30,
        "PT15M" => 15,
        _ => { panic!("don't know how to decode resolution string {}", resolution) },
    }
}

pub fn prod_name_from_psrt(psrt: &str) -> &str {
    match psrt {
        "B01" =>  "biomass",
        "B02" =>  "fossil_brown", 
        "B03" =>  "fossil_coal_derived_gas", 
        "B04" =>  "fossil_gas",
        "B05" =>  "fossil_hard_coal",
        "B06" =>  "fossil_oil",
        "B07" =>  "fossil_oil_shale",
        "B08" =>  "fossil_peat", 
        "B09" =>  "geothermal",
        "B10" =>  "hydro_pumped_storage", 
        "B11" =>  "hydro_run_of", 
        "B12" =>  "hydro_reservoir", 
        "B13" =>  "marine",
        "B14" =>  "nuclear", 
        "B15" =>  "other_renewable", 
        "B16" =>  "solar", 
        "B17" =>  "waste", 
        "B18" =>  "wind_offshore", 
        "B19" =>  "wind_onshore", 
        "B20" =>  "other_any",

        (s) => { log::debug!("unaccounted energy type: [{psrt}]"); s }
    }
}

