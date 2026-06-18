
# Energy Production Data Service

Server implementation for providing energy production information based on data retrieved from [transparency.entsoe.eu](https://transparency.entsoe.eu),
in the following documentation being referred to as ```eprofiler```.

The eprofiler service takes energy production generation and energy production prediction timeseries data from ENTSOE and processes those.
Following tasks may be performed:
- maps energy production market place data to geographic locations
- accumulates (sums up) energy generation data per production type time series into a single energy generation value over a given time period
- filters production type time series into relevant subset for further processing
- calculates proportions of energy generation production types in relation of the overall 
  generation amount, either per each time series data point or overall time period
- estimates CO2 equivalents of an energy production time series or interval according to production type  

## Repository Structure

### Directories:
- ```./examples```: command line clients sending test data to the server
- ```./src```:  rust source files
    - ```./src/aggregation```: production data processiong, aggregation, proportionalization, time series data interpolation, CO2eq emission calculation
    - ```./src/entsoe```: ENTSOE client implementation
    - ```./src/server```: http server, REST API and test GUI implementation
- ```./target```: build artifacts ("binaries")
- ```./www/static```: html files for serving test GUI
- ```./xml```: ENTSOE request examples for generating rust types
- ```./resources```: resources (e.g. images) used in documentation files

### Files:
- ```./README.md```: eprofiler documentation, this file
- ```./README-deployment.md```: all in all N-Ergy View server documentation 
- ```./config.json```: for eprofiler server configuration, e.g. ENTSOE API key
-  ```./Dockerfile``` docker build config
- ```./Dockerfile_full``` *(deprecated)*
- ```./Dockerfile_slim``` *(deprecated)*
- other: the usual rust project environment files

## Build

### local:
	- cargo build / cargo run
	- examples cargo run --example \[name of the source file\]

### docker:
	- docker build
	- docker image ls to obtain image_id
	- docker run image_id

## Deployment

To manually deploy the eprofiler at eddie.caosylab.at do the following:

```bash
cd /opt/eddie/repositories/eddie-entsoe-integration/
sudo docker container ls # to obtain container id, e.g.: 173459cffda5
sudo docker container stop 173459cffda5
git pull
sudo docker build -t eprofiler-slim_v06 .
sudo docker image ls # to obtain image id, e.g.: 275159effee9
sudo docker run -p8008:8000 275159effee9
# verify and restart container in portainer GUI
```
### Configuration

To set listening port and IP address, ENTSOE API URL and the security token to
be able to access it, enter the relevant data in the config.json file as depicted below.
The file must reside in the same directory in which eprofiler is executed.

```json
{
    "description": "about the configuration",
    "url": "0.0.0.0",
    "port": 8000,
    "entsoe-api-url": "https://web-api.tp.entsoe.eu/api",
    "security-token": "token obtained from entsoe.eu",

    "log-level": "DEBUG"
}
```

For global N-Ergy View server configuration details, please refer to: [README-deployment.md](./README-deployment.md).

### Local Execution examples

#### Test and Deploy

- execution of emission example client:
```
RUST_LOG=debug cargo run --example emission
```
- accessing the test GUI in borwser:
```
http://localhost:8000/gui
```


#### Usage

- build
```
cargo build
```

- execute:
```
RUST_LOG=debug cargo run
```

In browser navigate to: http://localhost:8000/api/production-by-type


### Example API requests:


http://localhost:8000/energymix?location="10YAT-APG------L"&start=202407242200&end=202407252200


## Implementation Notes

### ENTSOE Client

This eprofiler server uses the [ENTSOE](https://entsoe.eu) web service for central collection and publication of electricity generation, 
transportation and consumption data and information for the pan-European market. Data available is described  [here](https://eepublicdownloads.entsoe.eu/clean-documents/Transparency/MoP_Ref2_DDD_v3r4.pdf).



### CO2 Equivalent Emission Approximation Calculation

Lifecycle emission data are taken from the IPCC (2014) Fifth Assessment Report
Appendix III: Technology-specific Cost and Performance Parameters
(see: https://www.ipcc.ch/site/assets/uploads/2018/02/ipcc_wg3_ar5_annex-iii.pdf#page=7)
values in:  (gCO2eq / kW/h). The production types described there needed to be mapped to the
categorization used by ENTSOE (i.e. the CIM model)

**Deriving CO2eq emission:**
```rust
//m = 1.000.000, k = 1.000, h => 1 hour = 60 min
emission * [gCO2eq/kW/h] * energy * [mW] / (duration * [h]) 
emission * energy * [gCO2eq/kW/h] * [mW] / (duration * [h])
emission * energy * [gCO2eq/kW/h * mW * 1/h] / duration
emission * energy * [gCO2eq/(kW*1/h) * mW * 1/h] / duration
emission * energy * [gCO2eq/kW * mW] / duration
emission * energy * [(gCO2eq * mW)/kW] / duration
emission * energy * [gCO2eq * m/k] / duration
emission * energy * [gCO2eq * k] / duration
emission * energy / duration * [kgCO2eq]
```

### Production Type Mapping

Productiontype mapping from ENTSOE (CIM) production types to CO2eq defined production types takes place in [src/aggregation/schema.rs](./src/aggregation/schema.rs).

The mapping is a follows:

| ENTSOE/CIM | IPCC |
|:----|:-----|
| biomass | BiomassCofiring |
| fossil_brown | Coal | 
| fossil_coal_derived_gas | Coal | 
| fossil_gas | Gas |
| fossil_hard_coal | Coal |
| fossil_oil | OilGuess |
| fossil_oil_shale | OilGuess |
| fossil_peat | OilGuess |
| geothermal | Geothermal |
| hydro_pumped_storage | Hydropower | 
| hydro_run_of | Hydropower |
| hydro_reservoir | Hydropower | 
| marine | Ocean |
| nuclear | Nuclear | 
| solar | SolarGeneric | 
| wind_offshore | WindOffshore | 
| wind_onshore | WindOnshore |
| other | Unknown |

**NOTE:**  Both CO2eq calculation as well as production type mapping serve demonstration purposes only and are not to be referred to
in real scenarios.

### Time Series interval interpolation

The ENTSOE client does not handle requested time intervals strictly. Even if an inteval of
15 minutes is requested, depending on the marketplace (i.e. location) a time series with
different intervals between data points is returned. Therefore, the eprofiler server performs
datapoint interpolation for missing intervals. E.g. if data in an hourly interval are returned
by ENTSOE, however, 15 Munites intervals have been requested, the eprofiler would distribute a
1 hour value over 4 15 minutes values to be returned to its client.


### XML request / response XML handling

Using ENTSOE API : https://web-api.tp.entsoe.eu/api

### XML Schema Generator

Use the rust xml schema generator to produce rust types representing the xml data.

- download the schema generator code

    - Complete list: https://github.com/Thomblin/xml_schema_generator/releases

    - Best to unpack source file and build from scratch: https://github.com/Thomblin/xml_schema_generator/archive/refs/tags/0.6.12.zip


- invoke the schema generator:

    - see project [xml_schema_generator-0.6.12](https://git01lab.cs.univie.ac.at/cosy/eddie_playground/-/tree/main/rust/xml_schema_generator-0.6.12?ref_type=heads)

```
./xml_schema_generator entsoe_ex1.xml -p serde-xml-rs -d "Debug, Serialize, Deserialize" > entsoe_schema.rs

```

The following two example responses where used to generate the rust types:

- for parsing production generation responses: [xml/generation_by_type.xml](./xml/generation_by_type.xml)

- for parsing production prediction responses: [xml/prediction.xml](./xml/prediction.xml)


## Server Architecture, Interface and Datamodel

### REST API definition

#### GET /api/production-by-type

**Parameters:**

- ```zone```, ```start```, ```end```, ```aggregate```

#### GET /api/production-prediction

**Parameters:**

- ```zone```, ```start```, ```end```, ```aggregate```

#### POST /api/energy-mix-series

- **Input:**

```json
{ 
    "zone": "AT",
    "start": "202408192200",
    "end": "202408192300",
    "unit": "kWh", 
    "resolution": "PT15M",
    "consumption": [0.441, 0.444, 0.104, 0.088] 
}
```

#### POST /api/emission-series

- **Input:**

```json
{ 
    "zone": "AT",
    "start": "202408192200",
    "end": "202408192300",
    "unit": "kWh", 
    "resolution": "PT15M",
    "consumption": [0.441, 0.444, 0.104, 0.088] 
}
```

#### Parameter content format and content

- ```zone```, one of:
    - EU, AT, DE, FR, BE, DK, UK, HU, TR, IS, SE, NO, PL, IT, ES
    - or the domain string according to ENTSOE schema 

- ```start```
    - 12 digit timedate information, e.g.: 202408102300

- ```end```
    - 12 digit timedate information, e.g.: 202408110800

- ```aggregate```, one of:
    - Quantity
    - Proportion
    - Emission
    - QuantitySeries
    - ProportionSeries
    - EmissionSeries

#### ENTSOE Connection (Direct ENTSOE request examples)

```bash
curl --location 'https://web-api.tp.entsoe.eu/api?documentType=A65&processType=A16&outBiddingZone_Domain=10YCZ-CEPS-----N&periodStart=202303030000&periodEnd=202303060000&securityToken=11111111-1111-1111-1111-111111111111'
```

#### Example "Actual Generation per Production Type":

```bash
curl --location 'https://web-api.tp.entsoe.eu/api?documentType=A75&processType=A16&in_Domain=10YAT-APG------L&periodStart=202308152200&periodEnd=202308162200&securityToken=11111111-1111-1111-1111-111111111111'
```

Following the CIM model for energy data, ENTSOE uses the so called *psrType* (i.e. Production Type) 
in its response to to label the energy production source. Following 3 digit acronyms are used:
- B01 = Biomass;
- B02 = Fossil Brown coal/Lignite; 
- B03 = Fossil Coal-derived gas; 
- B04 = Fossil Gas; 
- B05 = Fossil Hard coal; 
- B06 = Fossil Oil; 
- B07 = Fossil Oil shale; 
- B08 = Fossil Peat; 
- B09 = Geothermal; 
- B10 = Hydro Pumped Storage; 
- B11 = Hydro Run-of-river and poundage; 
- B12 = Hydro Water Reservoir; 
- B13 = Marine; 
- B14 = Nuclear; 
- B15 = Other renewable; 
- B16 = Solar; 
- B17 = Waste; 
- B18 = Wind Offshore; 
- B19 = Wind Onshore; 
- B20 = Other


#### Example "production and generation units":

```bash
curl --location 'https://web-api.tp.entsoe.eu/api?documentType=A95&businessType=B11&BiddingZone_Domain=10YBE----------2&Implementation_DateAndOrTime=2017-01-01&securityToken=11111111-1111-1111-1111-111111111111'
```


#### Production generation request:

```bash
curl --location 'https://web-api.tp.entsoe.eu/api?documentType=A71&processType=A01&in_Domain=10YCZ-CEPS-----N&periodStart=201512312300&periodEnd=201612312300&securityToken=11111111-1111-1111-1111-111111111111'
```

A full set request examples can be found [here](https://gitlab.entsoe.eu/transparency/xml-examples).

## Installation for local development

### Tool chain for rust

- install rustup 
- call rustup to install toolchain

To get started, issue the follwing command, which will download and execute the one stop installation script:
```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```


## Technology Stack

- rust toolchain
- reqwest (rust web client)
- actix (rust web server)
- xml_schema_generator (rust xml schema generator)
- HTMX (direct browser/JS functianality access from HTML)
- Docker
- EDDIE CIM Model

