# Qdrant points — ES2012RS02.pdf

- points (rows upserted): **18**
- embedded: **True** · model `text-embedding-3-large` · dim 3072

Each point is `{id, vector, payload}` exactly as `index_chunks` upserts it. Children carry their embedding; parents carry a zero vector and are reached through their children. Below, vectors are truncated and `chunk_text` is clipped — see `05_qdrant_points.json` for the full data.

---

## Child · `ffcdad11-10ab-50d0-a5e9-3e153801158b`

- vector: dim=3072 · [-0.0217, -0.0175, -0.0101, 0.0101, -0.0123, 0.0030, -0.0387, 0.0084, …]

```json
{
  "chunk_id": "ffcdad11-10ab-50d0-a5e9-3e153801158b",
  "document_id": "es2012rs02_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ES2012RS02.pdf",
  "chunk_text": "Relative Environment Economics Of Natural Gas and \nOther Fossil Fuels for Power Generation and Policy \nOptions for India\n\nA Petroleum Federation Of India Study\n\nThe Energy and Resources Institute (Knowledge Partner) \nNew Delhi\n\nOverview\n\nBackground \nDescription of the study and findings \nCarbon Implications of power generation \nDomestic coal and gas availability and projected \nrequirements \nInternational fuel markets \nConclusions \nSuggestions – Policy Options \nExclusion – nuclear, renewables, clean coal, hydro\n\nBackground\n\nGrowing demand for power in India\n\nConstraints on supply of f\n\n… [+463 more chars]",
  "content_hash": "1ce4948a88674ecc372d60abe7647375eb2e02d2c0ca228de924da29dc32c694",
  "token_count": 226,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "es2012rs02_pdf",
  "pdf_path": "ES2012RS02.pdf",
  "chunk_index": 0,
  "page_number": 1,
  "page_range": [
    1,
    3
  ],
  "created_at": "2026-06-30T08:33:01.181752+00:00",
  "updated_at": "2026-06-30T08:33:01.181752+00:00"
}
```

## Child · `77036ff1-3d87-5896-a318-46737ff77520`

- vector: dim=3072 · [-0.0244, 0.0029, 0.0066, 0.0454, -0.0268, 0.0024, -0.0361, 0.0114, …]

```json
{
  "chunk_id": "77036ff1-3d87-5896-a318-46737ff77520",
  "document_id": "es2012rs02_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ES2012RS02.pdf",
  "section_heading": "India‟s Power Sector",
  "chunk_text": "\nInstalled capacity in the country is based largely \non coal \n\nAddition to capacity has been slower than planned \nwith large gap between target and actual \naddition \n\nAvailability of domestic fuel – a major factor \nconstraining the production of power in India in the \npast few years \nStagnating domestic coal production \nDeclining gas production\n\n\nA generating loss of 11.7 Billion Units reported up \nto January 2013 due to shortage of coal supplies \n\nGas shortages have also affected power \ngeneration \n\nSupply of gas up to January 2013 was 41.45 \nmmscmd as against a requirement of 86 mmsc\n\n… [+2 more chars]",
  "content_hash": "83271e69e0c6cade3d08207f7a9d91d0fc0ce560da268c00990cbf8bdf991b37",
  "token_count": 154,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "es2012rs02_pdf",
  "pdf_path": "ES2012RS02.pdf",
  "chunk_index": 1,
  "page_number": 4,
  "page_range": [
    4,
    4
  ],
  "created_at": "2026-06-30T08:33:01.181752+00:00",
  "updated_at": "2026-06-30T08:33:01.181752+00:00"
}
```

## Child · `070bdaa1-5597-51ba-8f30-5f504bdc3bc1`

- vector: dim=3072 · [-0.0307, -0.0064, -0.0106, 0.0122, -0.0142, -0.0130, -0.0386, 0.0190, …]

```json
{
  "chunk_id": "070bdaa1-5597-51ba-8f30-5f504bdc3bc1",
  "document_id": "es2012rs02_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ES2012RS02.pdf",
  "section_heading": "The Study",
  "chunk_text": "Comparison of the cost of power generation using different fuels (i.e. coal \nand gas both domestic and international) across various locations in the \ncountry\n\nIncluding the cost of carbon emissions generated in the process of extraction \nand combustion of fuel\n\nNeed to plan the energy future based on evolving international market \ndynamics of coal and gas while also accounting for the impact of energy on \nclimate\n\nCalculating the Cost of Power Generation \n\nBasic assumptions: \n9 locations across the country \nCombination of pithead, port based \nand inland power stations \nDependence on a \n\n… [+232 more chars]",
  "content_hash": "54feef5a4545e201c055f62c48f90123d5bfaf89c8e74eb35affbf989e7fcb74",
  "token_count": 196,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "es2012rs02_pdf",
  "pdf_path": "ES2012RS02.pdf",
  "chunk_index": 2,
  "page_number": 5,
  "page_range": [
    5,
    6
  ],
  "created_at": "2026-06-30T08:33:01.181752+00:00",
  "updated_at": "2026-06-30T08:33:01.181752+00:00"
}
```

## Child · `e4edf7d8-9a60-5a8a-bf30-6c06d3f40ae9`

- vector: dim=3072 · [-0.0303, -0.0167, -0.0017, 0.0571, -0.0185, -0.0278, -0.0423, 0.0146, …]

```json
{
  "chunk_id": "e4edf7d8-9a60-5a8a-bf30-6c06d3f40ae9",
  "document_id": "es2012rs02_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ES2012RS02.pdf",
  "section_heading": "Assumptions — Element — Unit — Domestic — Coal — Imported — Coal — Domestic — Gas — LNG — Heat rate",
  "chunk_text": "kcal/kWh \n2500 \n2500 \n2000 \n2000 \nCapital cost \nRs. \nAssumptions for power generation costs are based on norms specified by CERC (for 2009-14) \n•\nExchange rate – Rs 52.2/US$ as on August 2012  \n*The variation in prices is due to difference in transportation costs \nPrices for domestic coal are as on January 2012, other charges for 2010-11 \n(Source: Coal Directory of India), prices of domestic gas are for KG D6 gas and \nAPM gas,  imported gas prices are for July-August, 2012 and imported coal – \naverage for 2011-12 (Source: Coal Spot)\n\n| Element | Unit | Domestic Coal | Imported Coal | Domestic \n\n… [+639 more chars]",
  "content_hash": "0b952a64d35e09d312e36aefd98140615a28fa38b17f4ee28b7a41323435ef5e",
  "token_count": 439,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "es2012rs02_pdf",
  "pdf_path": "ES2012RS02.pdf",
  "chunk_index": 3,
  "page_number": 7,
  "page_range": [
    7,
    7
  ],
  "created_at": "2026-06-30T08:33:01.181752+00:00",
  "updated_at": "2026-06-30T08:33:01.181752+00:00"
}
```

## Child · `76a9a9f1-e21e-5938-89cc-daa60b51c8fe`

- vector: dim=3072 · [-0.0256, -0.0053, -0.0085, 0.0273, -0.0326, 0.0002, -0.0220, 0.0037, …]

```json
{
  "chunk_id": "76a9a9f1-e21e-5938-89cc-daa60b51c8fe",
  "document_id": "es2012rs02_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ES2012RS02.pdf",
  "section_heading": "Financial Cost of Power Generation",
  "chunk_text": "\nDomestic coal based generation at pit head power plants is less expensive than \nnon-pit head coal based generation\n\n\nImported coal is not as competitive as domestic coal due to its higher costs\n\n\nDomestic gas based power generation is more expensive than domestic coal based \ngeneration at all locations\n\n\nAt locations away from the pithead, the difference between the cost of power \ngenerated using the two fuels reduces substantially. These are Delhi, Vadodara, \nKochi and Agartala\n\n\nLNG is the most expensive fuel for power generation due to the high costs of fuel \nand the prevailing exchan\n\n… [+7 more chars]",
  "content_hash": "fa6c6a02e0a6be022b2827bbd11a71b1fbee449e202b1b0dbb50509a88007f04",
  "token_count": 137,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "es2012rs02_pdf",
  "pdf_path": "ES2012RS02.pdf",
  "chunk_index": 4,
  "page_number": 8,
  "page_range": [
    8,
    8
  ],
  "created_at": "2026-06-30T08:33:01.181752+00:00",
  "updated_at": "2026-06-30T08:33:01.181752+00:00"
}
```

## Child · `de0b917e-94d3-52bf-9a9b-16cb106a43a4`

- vector: dim=3072 · [-0.0065, -0.0207, -0.0105, 0.0314, -0.0309, -0.0078, -0.0186, 0.0247, …]

```json
{
  "chunk_id": "de0b917e-94d3-52bf-9a9b-16cb106a43a4",
  "document_id": "es2012rs02_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ES2012RS02.pdf",
  "section_heading": "Financial Cost of Power Generation",
  "chunk_text": "| Plant Locations | Fuel Options |  |  |  |\n| --- | --- | --- | --- | --- |\n|  | Domestic Coal | Imported Coal | Domestic Gas | LNG |\n| Delhi | 3.38 | 5.47 | 3.67 | 6.38 |\n| Bilaspur | 2.52 | 5.35 | 3.91 | 6.36 |\n| Vadodara | 3.18 | 5.16 | 3.60 | 6.31 |\n| Vishakapatnam | 2.86 | 4.93 | 3.55 | 6.12 |\n| Kochi | 3.85 | 5.10 | 3.97 | 6.12 |\n| Talcher | 2.52 | 4.98 | 3.91 | 6.33 |\n| Dhanbad | 2.68 | 5.09 | 3.95 | 6.38 |\n| Agartala | 3.73 | 5.75 | 3.97 | 6.38 |\n| Nagpur | 3.52 | 5.35 | 3.63 | 6.28 |",
  "content_hash": "790d35d4ed95d4383536e0200217d5aabf28dd801c097dcc5076f21887127a06",
  "token_count": 259,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "es2012rs02_pdf",
  "pdf_path": "ES2012RS02.pdf",
  "chunk_index": 5,
  "page_number": 9,
  "page_range": [
    9,
    9
  ],
  "created_at": "2026-06-30T08:33:01.181752+00:00",
  "updated_at": "2026-06-30T08:33:01.181752+00:00"
}
```

## Parent · `a888c55e-c7e3-5f34-a577-6b5d500adf8e`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "a888c55e-c7e3-5f34-a577-6b5d500adf8e",
  "document_id": "es2012rs02_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "ES2012RS02.pdf",
  "section_heading": "Carbon Implications — Carbon Emissions and Power Generation",
  "chunk_text": "Carbon Implications — Carbon Emissions and Power Generation\n\n\nElectricity generation contributes the largest \nshare to carbon emissions in India \n\nCarbon is emitted in the process of extraction \nof resource and during burning of fuel during \npower production \n\nCarbon emitted in the process of coal based \npower generation is nearly twice that of gas \nbased generation \n\nThese costs are internalised while computing \nthe final cost of power generation \n\nThere are other impacts on the environment \ngenerated \nin \nthe \nprocess \nof \npower \nproduction but these are not incorporated in \nthe current\n\n… [+4921 more chars]",
  "content_hash": "d2e6378412134b2a994492aa13380be89c12c5aa7f917f00f76fd79548227d9a",
  "token_count": 1857,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "es2012rs02_pdf",
  "pdf_path": "ES2012RS02.pdf",
  "page_range": [
    11,
    19
  ],
  "created_at": "2026-06-30T08:33:01.181752+00:00",
  "updated_at": "2026-06-30T08:33:01.181752+00:00"
}
```

## Child · `8c08714e-4a44-5c35-a054-5d7fbb96d295`

- vector: dim=3072 · [0.0033, -0.0182, 0.0031, -0.0142, -0.0229, -0.0185, -0.0270, -0.0162, …]

```json
{
  "chunk_id": "8c08714e-4a44-5c35-a054-5d7fbb96d295",
  "document_id": "es2012rs02_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ES2012RS02.pdf",
  "section_heading": "Carbon Implications — Carbon Emissions and Power Generation",
  "chunk_text": "\nElectricity generation contributes the largest \nshare to carbon emissions in India \n\nCarbon is emitted in the process of extraction \nof resource and during burning of fuel during \npower production \n\nCarbon emitted in the process of coal based \npower generation is nearly twice that of gas \nbased generation \n\nThese costs are internalised while computing \nthe final cost of power generation \n\nThere are other impacts on the environment \ngenerated \nin \nthe \nprocess \nof \npower \nproduction but these are not incorporated in \nthe current exercise\n\nElectricity, \n715.83, 51% \nTransport, \n138.86, 10%\n\n… [+230 more chars]",
  "content_hash": "036f17ffbe582810f3f5ad9bf5d3adcf21422031032cc68af9ba87d4db7e5ab0",
  "token_count": 224,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "es2012rs02_pdf",
  "pdf_path": "ES2012RS02.pdf",
  "parent_chunk_id": "a888c55e-c7e3-5f34-a577-6b5d500adf8e",
  "chunk_index": 6,
  "page_number": 11,
  "page_range": [
    11,
    11
  ],
  "created_at": "2026-06-30T08:33:01.181752+00:00",
  "updated_at": "2026-06-30T08:33:01.181752+00:00"
}
```

## Child · `73703b23-20f5-59f8-bcba-2c2b3ec1657e`

- vector: dim=3072 · [-0.0029, -0.0215, 0.0001, 0.0471, 0.0016, -0.0298, -0.0471, 0.0145, …]

```json
{
  "chunk_id": "73703b23-20f5-59f8-bcba-2c2b3ec1657e",
  "document_id": "es2012rs02_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ES2012RS02.pdf",
  "section_heading": "Carbon Implications — Carbon Emissions and Power Generation",
  "chunk_text": "92, 9% \nIron and \nSteel, \n116.96, 9% \nOther \nindustries, \n158.98, 11% \nCO2 emissions distribution (million tonnes) across \nsectors in 2007 \nSource: Planning Commission , 2011 Calculating the Cost of Carbon \nThere has been significant volatility in carbon prices \nCurrent Carbon Emission Reduction (CER) prices in European Emission \nTrading Scheme (ETS) have been affected by prevailing macroeconomic \nand market situation and have declined substantially in 2011-12 \nPrices of carbon are based on the concept of Social Cost of Carbon – \nproposed by the Stern Review \nDifferent levels of social cos\n\n… [+716 more chars]",
  "content_hash": "e26bff8e47ad76a80bdfc1806e0396f5f73b0b9a5d0ae822765fbc11cd2f2dd8",
  "token_count": 346,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "es2012rs02_pdf",
  "pdf_path": "ES2012RS02.pdf",
  "parent_chunk_id": "a888c55e-c7e3-5f34-a577-6b5d500adf8e",
  "chunk_index": 7,
  "page_number": 12,
  "page_range": [
    12,
    13
  ],
  "created_at": "2026-06-30T08:33:01.181752+00:00",
  "updated_at": "2026-06-30T08:33:01.181752+00:00"
}
```

## Child · `67733f0d-abdb-5766-b5e5-b77a49577588`

- vector: dim=3072 · [-0.0079, -0.0152, -0.0030, 0.0435, -0.0339, 0.0044, -0.0272, 0.0231, …]

```json
{
  "chunk_id": "67733f0d-abdb-5766-b5e5-b77a49577588",
  "document_id": "es2012rs02_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ES2012RS02.pdf",
  "section_heading": "Carbon Implications — Carbon Emissions and Power Generation",
  "chunk_text": "carbon tax of AU$ 23-25/tonne of CO2 to be followed by an ETS\n\nAdding the Cost of Carbon to Power Generation Costs (1) \nTotal cost of power generation at a carbon price of US$ 30/tCO2 (in Rs./kWh) | Plant Locations | Fuel Options |  |  |  |\n| --- | --- | --- | --- | --- |\n|  | Domestic Coal | Imported Coal | Domestic Gas | LNG |\n| Delhi | 4.97 | 7.02 | 4.41 | 7.11 |\n| Bilaspur | 4.11 | 6.91 | 4.65 | 7.09 |\n| Vadodara | 4.76 | 6.72 | 4.34 | 7.04 |\n| Vishakapatnam | 4.45 | 6.48 | 4.29 | 6.86 |\n| Kochi | 5.44 | 6.65 | 4.72 | 6.86 |\n| Talcher | 4.11 | 6.53 | 4.65 | 7.07 |\n| Dhanbad | 4.26 | 6.64 |\n\n… [+229 more chars]",
  "content_hash": "f55296e02781ff01958394c4cd8262b220868c64ddc62846a5071c11a68d846e",
  "token_count": 356,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "es2012rs02_pdf",
  "pdf_path": "ES2012RS02.pdf",
  "parent_chunk_id": "a888c55e-c7e3-5f34-a577-6b5d500adf8e",
  "chunk_index": 8,
  "page_number": 13,
  "page_range": [
    13,
    14
  ],
  "created_at": "2026-06-30T08:33:01.181752+00:00",
  "updated_at": "2026-06-30T08:33:01.181752+00:00"
}
```

## Child · `44219a8d-9d2b-5cba-82d4-3481586e68b4`

- vector: dim=3072 · [-0.0071, -0.0158, -0.0072, 0.0415, -0.0318, -0.0268, -0.0147, 0.0211, …]

```json
{
  "chunk_id": "44219a8d-9d2b-5cba-82d4-3481586e68b4",
  "document_id": "es2012rs02_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ES2012RS02.pdf",
  "section_heading": "Carbon Implications — Carbon Emissions and Power Generation",
  "chunk_text": "Nagpur | 4.47 | 6.90 | 4.38 | 7.02 |\n\nAdding the Cost of Carbon to Power Generation Costs (2) \nTotal cost of power generation at a carbon price of US$ 10/tCO2 (in Rs./kWh) | Plant Locations | Fuel Options |  |  |  |\n| --- | --- | --- | --- | --- |\n|  | Domestic Coal | Imported Coal | Domestic Gas | LNG |\n| Delhi | 3.91 | 5.98 | 3.92 | 6.62 |\n| Bilaspur | 3.05 | 5.87 | 4.15 | 6.60 |\n| Vadodara | 3.71 | 5.68 | 3.84 | 6.55 |\n| Vishakapatnam | 3.39 | 5.45 | 3.80 | 6.37 |\n| Kochi | 4.38 | 5.62 | 4.22 | 6.37 |\n| Talcher | 3.05 | 5.50 | 4.15 | 6.58 |\n| Dhanbad | 3.21 | 5.61 | 4.20 | 6.62 |\n| Agartala\n\n… [+395 more chars]",
  "content_hash": "5590ad34fb9c55025eca32ec66b5928d3cc355d0b504ebddbe76e5ee7d2d2dcb",
  "token_count": 387,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "es2012rs02_pdf",
  "pdf_path": "ES2012RS02.pdf",
  "parent_chunk_id": "a888c55e-c7e3-5f34-a577-6b5d500adf8e",
  "chunk_index": 9,
  "page_number": 14,
  "page_range": [
    14,
    15
  ],
  "created_at": "2026-06-30T08:33:01.181752+00:00",
  "updated_at": "2026-06-30T08:33:01.181752+00:00"
}
```

## Child · `4a62a11c-3875-5b45-9a61-ab362ce6bafc`

- vector: dim=3072 · [-0.0062, -0.0094, -0.0092, 0.0327, -0.0377, -0.0025, -0.0172, 0.0187, …]

```json
{
  "chunk_id": "4a62a11c-3875-5b45-9a61-ab362ce6bafc",
  "document_id": "es2012rs02_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ES2012RS02.pdf",
  "section_heading": "Carbon Implications — Carbon Emissions and Power Generation",
  "chunk_text": "Generation Cost (3) \nWhen the costs of carbon are incorporated:\n\nDomestic natural gas becomes competitive with domestic coal in most \nlocations\n\nThe difference between imported coal and LNG reduces substantially \nand LNG even becomes competitive in distant locations (such as \nAgartala) | Plant Locations | Fuel Options |  |  |  |  |  |\n| --- | --- | --- | --- | --- | --- | --- |\n|  | Imported Coal |  |  | LNG |  |  |\n|  | Without carbon cost | With carbon costs (at US$ 10) | With carbon costs (at US$ 30) | Without carbon cost | With carbon costs (at US$ 10) | With carbon costs (at US$ 30) |\n\n\n… [+552 more chars]",
  "content_hash": "aed4086830890382d28112ffdfb22b204733f9df79b3a6ee4d82a9d3d70e903b",
  "token_count": 484,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "es2012rs02_pdf",
  "pdf_path": "ES2012RS02.pdf",
  "parent_chunk_id": "a888c55e-c7e3-5f34-a577-6b5d500adf8e",
  "chunk_index": 10,
  "page_number": 16,
  "page_range": [
    16,
    17
  ],
  "created_at": "2026-06-30T08:33:01.181752+00:00",
  "updated_at": "2026-06-30T08:33:01.181752+00:00"
}
```

## Child · `ab72c2d8-8beb-5609-8848-69c1d776cc4e`

- vector: dim=3072 · [-0.0359, -0.0118, -0.0006, 0.0489, -0.0152, -0.0165, -0.0301, 0.0070, …]

```json
{
  "chunk_id": "ab72c2d8-8beb-5609-8848-69c1d776cc4e",
  "document_id": "es2012rs02_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ES2012RS02.pdf",
  "section_heading": "Carbon Implications — Carbon Emissions and Power Generation",
  "chunk_text": "| 6.38 | 6.62 | 7.11 |\n| Nagpur | 5.35 | 5.87 | 6.90 | 6.28 | 6.53 | 7.02 |\n\nDomestic Coal and Gas Availability and Projected Requirements Domestic Fuel Availability in India - \nCoal \nCoal and gas shortages in the country are constraining the development of \npower sector in the country\n\nThe reasons cited for shortages of coal are delay in obtaining clearances, \nbottlenecks in transport and evacuation facilities\n\nThe total requirement for non-coking coal is projected to increase to 913.3 \nMt (Million tonnes) by 2016-17 and further to 1268 Mt by 2021-22*\n\nEven if domestic production targets \n\n… [+701 more chars]",
  "content_hash": "043c8d24224f72df44a4470b6fc991f96aceb892db95ee9cef4f24d906c02eac",
  "token_count": 347,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "es2012rs02_pdf",
  "pdf_path": "ES2012RS02.pdf",
  "parent_chunk_id": "a888c55e-c7e3-5f34-a577-6b5d500adf8e",
  "chunk_index": 11,
  "page_number": 18,
  "page_range": [
    18,
    19
  ],
  "created_at": "2026-06-30T08:33:01.181752+00:00",
  "updated_at": "2026-06-30T08:33:01.181752+00:00"
}
```

## Child · `838896fa-862b-5480-b74d-27c663b06e39`

- vector: dim=3072 · [-0.0536, -0.0363, -0.0129, 0.0175, -0.0104, -0.0283, -0.0079, 0.0131, …]

```json
{
  "chunk_id": "838896fa-862b-5480-b74d-27c663b06e39",
  "document_id": "es2012rs02_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ES2012RS02.pdf",
  "section_heading": "International Fuel Markets — Changing Trends in International Markets",
  "chunk_text": "\nNeed to examine the international fuel \nmarkets and their evolution in the near to \nmedium term (5 to 10 years) \n\nDependence on international markets is \nrising for both coal and gas \n\nProduction of natural gas/shale oil and \ngas in North America – changing the flow \nof international energy trade \n\nNatural gas production in North America \n– likely to impact the fundamentals across \nEurope and Asia as well \n\nThis will have implications on the price of \nenergy \nsources \nin \nthe \ninternational \nmarkets \nPrice of Indian basket of crude oil",
  "content_hash": "5c4788460ad51a4c4d20336eebca4c5092d30dce7f7ceb66fb2e4010578f16ca",
  "token_count": 128,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "es2012rs02_pdf",
  "pdf_path": "ES2012RS02.pdf",
  "chunk_index": 12,
  "page_number": 21,
  "page_range": [
    21,
    21
  ],
  "created_at": "2026-06-30T08:33:01.181752+00:00",
  "updated_at": "2026-06-30T08:33:01.181752+00:00"
}
```

## Child · `a3964f09-20d1-5522-894a-3cd3d038e329`

- vector: dim=3072 · [-0.0216, -0.0068, -0.0091, 0.0132, -0.0272, -0.0106, -0.0110, 0.0031, …]

```json
{
  "chunk_id": "a3964f09-20d1-5522-894a-3cd3d038e329",
  "document_id": "es2012rs02_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ES2012RS02.pdf",
  "section_heading": "Global Coal Markets (1)",
  "chunk_text": "Coal continues to be a major source of energy – fastest growing source in \nabsolute terms in 2011  \nEurope has witnessed an increase in coal consumption – primarily driven by \nswitching from natural gas to coal fired power generation, exports from USA to \nEurope \nIn the immediate term, coal consumption in Europe is expected to increase \nAs per the IEA – in the medium term – coal usage in OECD Europe will stagnate \nwhereas that in OECD Asia/Oceania will rise marginally \nCoal demand in USA has declined substantially – due to decline in gas prices \nand ageing coal fired power plants \nDemand\n\n… [+1105 more chars]",
  "content_hash": "faadce73b3b6d865fba7d2c43bdc34d91dc9ee0874dd37745715707186c18a0e",
  "token_count": 447,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "es2012rs02_pdf",
  "pdf_path": "ES2012RS02.pdf",
  "chunk_index": 13,
  "page_number": 22,
  "page_range": [
    22,
    23
  ],
  "created_at": "2026-06-30T08:33:01.181752+00:00",
  "updated_at": "2026-06-30T08:33:01.181752+00:00"
}
```

## Child · `1501148f-f956-50ca-9833-1b0d159bd15c`

- vector: dim=3072 · [-0.0506, -0.0139, -0.0184, 0.0532, -0.0255, -0.0210, -0.0025, 0.0132, …]

```json
{
  "chunk_id": "1501148f-f956-50ca-9833-1b0d159bd15c",
  "document_id": "es2012rs02_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ES2012RS02.pdf",
  "section_heading": "Global Gas Markets",
  "chunk_text": "\n4 gas markets – North America, Europe,  Asia and Australia\n\n\nNatural gas prices in Asian markets - largely linked to crude oil prices\n\n\nProduction of shale gas in North America is altering the global gas markets\n\n\nUSA no longer dependent on imported LNG and is expected to now become an \nexporter\n\n\nLNG which was to be exported to USA will now be available to Europe and Asia \nAt lower rates?\n\n\nProgressive delinking of oil and gas prices in Europe – move towards gas on gas \ncompetition and pricing\n\n\nReports of gas contracts being renegotiated in these regions\n\n\nLikelihood of excess gas \n\n… [+45 more chars]",
  "content_hash": "95bda1bc6bfb1484b2cfd98ec91670e081c9dc74f04062831d8f65abd84cae59",
  "token_count": 155,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "es2012rs02_pdf",
  "pdf_path": "ES2012RS02.pdf",
  "chunk_index": 14,
  "page_number": 24,
  "page_range": [
    24,
    24
  ],
  "created_at": "2026-06-30T08:33:01.181752+00:00",
  "updated_at": "2026-06-30T08:33:01.181752+00:00"
}
```

## Child · `f9810318-41f6-50ea-b5d1-6e68f896d0e1`

- vector: dim=3072 · [-0.0320, -0.0074, -0.0045, 0.0182, -0.0242, -0.0119, -0.0480, 0.0155, …]

```json
{
  "chunk_id": "f9810318-41f6-50ea-b5d1-6e68f896d0e1",
  "document_id": "es2012rs02_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ES2012RS02.pdf",
  "section_heading": "Conclusions — Conclusions",
  "chunk_text": "The difference between cost of power generated using LNG and imported coal \nreduces if the carbon implications are taken into account \nIf the impact of increased shale gas availability in North America spreads to \nEurope and then to Asia, the rise in LNG prices may only be moderate \nThe tax etc. on coal exports from Australia and Indonesia are only likely to \nincrease,  making coal import costs higher \nThe climate change concerns and the National Action Plan on Climate Change \nalso warrant lowering emissions from power generation \nThe huge demand for fuel makes it imperative that we aband\n\n… [+757 more chars]",
  "content_hash": "313a335ab4163c264a36c811d6815dec686b5cb39d548b951fb707c67d4a4e27",
  "token_count": 275,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "es2012rs02_pdf",
  "pdf_path": "ES2012RS02.pdf",
  "chunk_index": 15,
  "page_number": 26,
  "page_range": [
    26,
    28
  ],
  "created_at": "2026-06-30T08:33:01.181752+00:00",
  "updated_at": "2026-06-30T08:33:01.181752+00:00"
}
```

## Child · `f3d0b003-0c5d-5024-b1b0-a9e7ee345a64`

- vector: dim=3072 · [-0.0256, 0.0194, -0.0057, -0.0047, -0.0282, -0.0245, -0.0383, 0.0161, …]

```json
{
  "chunk_id": "f3d0b003-0c5d-5024-b1b0-a9e7ee345a64",
  "document_id": "es2012rs02_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "ES2012RS02.pdf",
  "section_heading": "Coal",
  "chunk_text": "• Evacuation infrastructure in terms of rail networks to transport  \nmined coal to demand centres \nTransport infrastructure \n• Increasing the share of underground coal mining \nMining Technology \n• In-situ gasification is one of the most important ways to reach \ncoal at depths and to reduce the carbon impact \nUnderground coal \ngasification \n• Domestic coal is high in ash content \n• Current washery capacity for coal is only 33 Mt for coking \ncoal and 112 Mt for non-coking coal (2010-11, Coal Directory) \nWashery capacity \n• Port facilities \n• Rail links for in-land hauling of coal  \nImport infras\n\n… [+282 more chars]",
  "content_hash": "0c79b2e2b51085fce7de9cfa0e2d730e25879d16fa1b30e16ee9dc8805231212",
  "token_count": 196,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "es2012rs02_pdf",
  "pdf_path": "ES2012RS02.pdf",
  "chunk_index": 16,
  "page_number": 29,
  "page_range": [
    29,
    30
  ],
  "created_at": "2026-06-30T08:33:01.181752+00:00",
  "updated_at": "2026-06-30T08:33:01.181752+00:00"
}
```
