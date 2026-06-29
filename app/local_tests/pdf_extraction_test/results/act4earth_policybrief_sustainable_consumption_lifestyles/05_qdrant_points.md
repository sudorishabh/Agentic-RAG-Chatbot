# Qdrant points — Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf

- points (rows upserted): **35**
- embedded: **True** · model `text-embedding-3-large` · dim 3072

Each point is `{id, vector, payload}` exactly as `index_chunks` upserts it. Children carry their embedding; parents carry a zero vector and are reached through their children. Below, vectors are truncated and `chunk_text` is clipped — see `05_qdrant_points.json` for the full data.

---

## Child · `4a4870bf-7578-5c1e-b005-08591ee2d306`

- vector: dim=3072 · [-0.0092, -0.0018, -0.0179, -0.0326, -0.0193, -0.0065, 0.0048, 0.0121, …]

```json
{
  "chunk_id": "4a4870bf-7578-5c1e-b005-08591ee2d306",
  "document_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "section_heading": "ACT4EARTH — SDG CHARTER POLICY BRIEF — INTERNATIONALIZING — LIFESTYLES FOR — ENVIRONMENT — MESSAGES FOR G20",
  "chunk_text": "ISBN 978-93-94657-10-6\nAUTHORS\nShailly Kedia, Shweta Gautam, Manish Anand, Ishan Khetan, Nivedita Cholayil, Saheli Das\nREVIEWER\nProdipto Ghosh, Suneel Pandey\nACKNOWLEDGMENTS\nWe thank Bloomberg Philanthropies [Star Partner], the Rockefeller Foundation [Premier \nPartner], German Federal Ministry for the Environment, Nature Conservation, Nuclear \nSafety and Consumer Protection (BMUV) and International Climate Initiative (IKI) [Senior \nPartner], along with Tata Cleantech Capital Ltd [Associate Partner] for their support for the \nWorld Sustainable Development Summit and Act4Earth. We thank One Plan\n\n… [+695 more chars]",
  "content_hash": "285ff5147f4cf054dd5826437742c17742ad9c3b18cf77d1d69ba99e8348a535",
  "token_count": 298,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "pdf_path": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "chunk_index": 0,
  "page_number": 2,
  "page_range": [
    2,
    2
  ],
  "created_at": "2026-06-29T10:33:21.836822+00:00",
  "updated_at": "2026-06-29T10:33:21.836822+00:00"
}
```

## Parent · `3ab48be5-6b73-54a2-bbc0-80614dc3f4b8`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "3ab48be5-6b73-54a2-bbc0-80614dc3f4b8",
  "document_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "section_heading": "Introduction",
  "chunk_text": "Introduction\n\n6\nLifestyles and Consumption Index for G20 \t\n8\nInstruments to Nudge Lifestyles and Consumption \t\n11\nWay Forward: Internationalizing Lifestyles and Deploying Instruments\t\n15\nReferences\t\n18\nCONTENTS\n\nInternationalizing Lifestyles for Environment: Messages for G20\t\n5\nABSTRACT\nSustainable consumption and lifestyles must be seen from the perspective of resource value chains that \ninclude resource extraction, manufacturing, processing, use by consumer, and disposal. Mainstream \nframeworks on sustainable consumption and production focus more on upstream and mid-stream \ncomponents, such \n\n… [+8582 more chars]",
  "content_hash": "792f42616ffaf42f939fdf8e910954ba4f4d3d6090ea2bc3203f3f62afc45626",
  "token_count": 1789,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "pdf_path": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "page_range": [
    3,
    7
  ],
  "created_at": "2026-06-29T10:33:21.836822+00:00",
  "updated_at": "2026-06-29T10:33:21.836822+00:00"
}
```

## Child · `5911f148-fff8-5bee-a4c6-8105782e7901`

- vector: dim=3072 · [-0.0198, -0.0224, -0.0138, -0.0295, -0.0136, -0.0107, 0.0125, 0.0079, …]

```json
{
  "chunk_id": "5911f148-fff8-5bee-a4c6-8105782e7901",
  "document_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "section_heading": "Introduction",
  "chunk_text": "6\nLifestyles and Consumption Index for G20 \t\n8\nInstruments to Nudge Lifestyles and Consumption \t\n11\nWay Forward: Internationalizing Lifestyles and Deploying Instruments\t\n15\nReferences\t\n18\nCONTENTS\n\nInternationalizing Lifestyles for Environment: Messages for G20\t\n5\nABSTRACT\nSustainable consumption and lifestyles must be seen from the perspective of resource value chains that \ninclude resource extraction, manufacturing, processing, use by consumer, and disposal. Mainstream \nframeworks on sustainable consumption and production focus more on upstream and mid-stream \ncomponents, such as resource ef\n\n… [+1149 more chars]",
  "content_hash": "bcab04869e4500fd12586058b6cc8e0035415378b79bdd9651e94eaa5ad0c504",
  "token_count": 326,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "pdf_path": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "parent_chunk_id": "3ab48be5-6b73-54a2-bbc0-80614dc3f4b8",
  "chunk_index": 1,
  "page_number": 3,
  "page_range": [
    3,
    5
  ],
  "created_at": "2026-06-29T10:33:21.836822+00:00",
  "updated_at": "2026-06-29T10:33:21.836822+00:00"
}
```

## Child · `87815a3f-8947-599d-b9a0-e2eb45b932e7`

- vector: dim=3072 · [-0.0157, 0.0053, -0.0150, -0.0061, -0.0255, -0.0137, 0.0107, 0.0070, …]

```json
{
  "chunk_id": "87815a3f-8947-599d-b9a0-e2eb45b932e7",
  "document_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "section_heading": "Introduction",
  "chunk_text": "Implications for internationalizing lifestyles through G20, Global \nIndicator Framework for SDGs, and United Nations Framework Convention on Climate Change is then \ndiscussed.\nKeywords: SDG 12, lifestyles, sustainable consumption, G20, sustainable development, climate \nchange 6\t\nSDG Charter Policy Brief\nINTRODUCTION \nThere has been a focus on unsustainable patterns of production and consumption at the global level since \nthe adoption of Agenda 21: an outcome document of the United Nations Conference on Environment \nand Development (UNCED). It is clearly understood that sustainable production a\n\n… [+2068 more chars]",
  "content_hash": "53b67a5c91e0e6a10d19b9025bc71dd44cee740af5b062a337d16a6213e4d791",
  "token_count": 488,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "pdf_path": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "parent_chunk_id": "3ab48be5-6b73-54a2-bbc0-80614dc3f4b8",
  "chunk_index": 2,
  "page_number": 6,
  "page_range": [
    6,
    6
  ],
  "created_at": "2026-06-29T10:33:21.836822+00:00",
  "updated_at": "2026-06-29T10:33:21.836822+00:00"
}
```

## Child · `90c55f49-9bb2-536f-ad89-4dfa1cb1d1be`

- vector: dim=3072 · [-0.0308, 0.0144, -0.0171, 0.0040, -0.0255, -0.0362, 0.0094, -0.0236, …]

```json
{
  "chunk_id": "90c55f49-9bb2-536f-ad89-4dfa1cb1d1be",
  "document_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "section_heading": "Introduction",
  "chunk_text": "Sustainable consumer lifestyles or sustainable \nlifestyles is a part of the downstream segment of resource value chains. Based on the concept of sustainable \ndevelopment, a working definition of sustainable lifestyles proposed through this paper is “individual \nconsumer choices and attitudes towards the consumption of goods and services to further human well- being, spur innovations, while minimizing ecological footprint and waste so as to promote intragenerational \nand intergenerational equity for sustainable development”.  \nAccording to AR6 WG-III report of the Intergovernmental Panel on Cli\n\n… [+925 more chars]",
  "content_hash": "bf8ae1d67c8ebaf7ab1b7cb8f733844041896c3e716ac0d0f67d679c52f76ce4",
  "token_count": 358,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "pdf_path": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "parent_chunk_id": "3ab48be5-6b73-54a2-bbc0-80614dc3f4b8",
  "chunk_index": 3,
  "page_number": 6,
  "page_range": [
    6,
    6
  ],
  "created_at": "2026-06-29T10:33:21.836822+00:00",
  "updated_at": "2026-06-29T10:33:21.836822+00:00"
}
```

## Child · `51d0e2a6-ea4c-58d3-9058-9d55901d24a5`

- vector: dim=3072 · [-0.0200, -0.0086, -0.0109, 0.0143, -0.0385, -0.0125, -0.0248, 0.0027, …]

```json
{
  "chunk_id": "51d0e2a6-ea4c-58d3-9058-9d55901d24a5",
  "document_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "section_heading": "Introduction",
  "chunk_text": "26th United Nations Climate Change Conference \nResource\nExtrac\u001fon\nManufacturing/\nProcessing\nUse by\nConsumer\nDisposal\nPhase\nTransport, Design and Policy\nSustainable\nLifestyles\nFIGURE 1: SUSTAINABLE LIFESTYLES AND RESOURCE VALUE CHAINS Internationalizing Lifestyles for Environment: Messages for G20\t\n7\nof the Parties (COP26) in Glasgow last year. The idea promotes an environment-conscious lifestyle that \nfocuses on ‘mindful and deliberate utilisation’ instead of ‘mindless and destructive consumption’ through \nadvocating sustainable choices by  ‘Pro-Planet People’. Key concepts around LiFE include\n\n… [+1745 more chars]",
  "content_hash": "b4c367c14b86bdd23ab6877016ddb8cd7df63117028c48d63894fd7338e372e6",
  "token_count": 494,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "pdf_path": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "parent_chunk_id": "3ab48be5-6b73-54a2-bbc0-80614dc3f4b8",
  "chunk_index": 4,
  "page_number": 7,
  "page_range": [
    7,
    7
  ],
  "created_at": "2026-06-29T10:33:21.836822+00:00",
  "updated_at": "2026-06-29T10:33:21.836822+00:00"
}
```

## Child · `5d119d9a-f907-5b22-a8a6-27874acf75a5`

- vector: dim=3072 · [-0.0141, -0.0133, -0.0132, -0.0019, -0.0266, -0.0208, -0.0030, -0.0260, …]

```json
{
  "chunk_id": "5d119d9a-f907-5b22-a8a6-27874acf75a5",
  "document_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "section_heading": "Introduction",
  "chunk_text": "For example, intoxicants may be \nbanned, vaccination for contagious diseases may be mandatory, and people may be taxed for consuming \nharmful products, or given subsidies for consuming certain socially beneficial goods and services. An \nimportant aspect in influencing consumer choices is media advertisement. When it comes to individual choices, various perspectives are important. Governments may view individuals \nas constituents who are to be governed. Markets may view individuals as consumers whose purchasing \ndecisions are to be influenced. From the perspective of environmentalists, consumer\n\n… [+1457 more chars]",
  "content_hash": "3aba182eadba7eb645cc751db378214eee03e99fc81650b35446506f2d63ee48",
  "token_count": 348,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "pdf_path": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "parent_chunk_id": "3ab48be5-6b73-54a2-bbc0-80614dc3f4b8",
  "chunk_index": 5,
  "page_number": 7,
  "page_range": [
    7,
    7
  ],
  "created_at": "2026-06-29T10:33:21.836822+00:00",
  "updated_at": "2026-06-29T10:33:21.836822+00:00"
}
```

## Parent · `15087c98-5307-58a7-9a32-1fd99e4c23ba`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "15087c98-5307-58a7-9a32-1fd99e4c23ba",
  "document_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "section_heading": "Introduction",
  "chunk_text": "Introduction (cont.)\n\n8\t\nSDG Charter Policy Brief\nLIFESTYLES AND CONSUMPTION INDEX FOR G20 \nTo understand the state of lifestyles and consumption for G20 countries and the European Union, a composite \nindex and indices on consumption sectors (such as food, transport, residential and waste management) \nhave been developed. Table 1 summarises the indicators used in calculating the metrics for G20 countries \nand the European Union. \nTABLE 1: INDICATORS AND DATA SOURCES USED FOR DEVELOPING METRICS ON SUSTAINABLE \nCONSUMPTION\nSector\nIndicator\nData source\nYear\nTransport\nTotal final energy \nconsumpti\n\n… [+3858 more chars]",
  "content_hash": "885b523e728748edc80b3d6133fe7dbcdd5f9aaa2cead1b78398676f6744e467",
  "token_count": 1153,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "pdf_path": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "page_range": [
    8,
    9
  ],
  "created_at": "2026-06-29T10:33:21.836822+00:00",
  "updated_at": "2026-06-29T10:33:21.836822+00:00"
}
```

## Child · `945fd016-eb6d-5d49-bde7-2a839822c112`

- vector: dim=3072 · [-0.0141, 0.0145, -0.0061, -0.0230, -0.0229, -0.0324, 0.0154, 0.0217, …]

```json
{
  "chunk_id": "945fd016-eb6d-5d49-bde7-2a839822c112",
  "document_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "section_heading": "Introduction",
  "chunk_text": "8\t\nSDG Charter Policy Brief\nLIFESTYLES AND CONSUMPTION INDEX FOR G20 \nTo understand the state of lifestyles and consumption for G20 countries and the European Union, a composite \nindex and indices on consumption sectors (such as food, transport, residential and waste management) \nhave been developed. Table 1 summarises the indicators used in calculating the metrics for G20 countries \nand the European Union. \nTABLE 1: INDICATORS AND DATA SOURCES USED FOR DEVELOPING METRICS ON SUSTAINABLE \nCONSUMPTION\nSector\nIndicator\nData source\nYear\nTransport\nTotal final energy \nconsumption in \ntransport secto\n\n… [+535 more chars]",
  "content_hash": "b23c7c965b6ee77950acc7ea82146ecb32b0121e6495b7c32c69bb0ef9dbe71a",
  "token_count": 294,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "pdf_path": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "parent_chunk_id": "15087c98-5307-58a7-9a32-1fd99e4c23ba",
  "chunk_index": 6,
  "page_number": 8,
  "page_range": [
    8,
    8
  ],
  "created_at": "2026-06-29T10:33:21.836822+00:00",
  "updated_at": "2026-06-29T10:33:21.836822+00:00"
}
```

## Child · `fbbf2ad2-43e4-5c7f-8a61-04a1853a00e4`

- vector: dim=3072 · [-0.0289, -0.0091, -0.0049, -0.0157, -0.0246, -0.0640, 0.0165, 0.0176, …]

```json
{
  "chunk_id": "fbbf2ad2-43e4-5c7f-8a61-04a1853a00e4",
  "document_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "section_heading": "Introduction",
  "chunk_text": "8\nResidential Buildings\nTotal final energy \nconsumption in \nresidential sector (TJ/\ncapita)\t\nIEA World Energy Balances \nhttps://www.iea.org/data-and-\nstatistics/data-product/world-\nenergy-statistics-and-balances\n2019\nWaste Disposal Plastic waste generation \n(tonnes/capita)\nSource: Jambeck et al (2015) \nin https://ourworldindata.\norg/grapher/plastic-waste-\ngeneration-total; Eurostat\n2010 and 2015\nThe choice of index is based on key sectors that have been extensively covered in the literature and contribute \nsignificantly to sustainable consumption on the downstream or end-consumer side. The dow\n\n… [+1527 more chars]",
  "content_hash": "1613d16763b058c0ec3996eb07e6f65e2ab934fafa611639a265acea9465406c",
  "token_count": 471,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "pdf_path": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "parent_chunk_id": "15087c98-5307-58a7-9a32-1fd99e4c23ba",
  "chunk_index": 7,
  "page_number": 8,
  "page_range": [
    8,
    8
  ],
  "created_at": "2026-06-29T10:33:21.836822+00:00",
  "updated_at": "2026-06-29T10:33:21.836822+00:00"
}
```

## Child · `f19d0f2e-5144-5dfc-b157-69c1e4f0dc30`

- vector: dim=3072 · [-0.0206, 0.0075, -0.0090, -0.0028, -0.0189, -0.0856, -0.0056, 0.0097, …]

```json
{
  "chunk_id": "f19d0f2e-5144-5dfc-b157-69c1e4f0dc30",
  "document_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "section_heading": "Introduction",
  "chunk_text": "For scoring, the standardized values are then multiplied by 100 to arrive at scores. These are then depicted \ngraphically (Figure 2). The higher the score, the lower the consumption is in per capita terms for the individual. | and the European Union. |  |  |  |\n| --- | --- | --- | --- |\n| TABLE 1: INDICATORS AND DATA SOURCES USED FOR DEVELOPING METRICS ON SUSTAINABLE |  |  |  |\n| CONSUMPTION |  |  |  |\n| Sector | Indicator | Data source | Year |\n| Transport | Total final energy | IEA World Energy Balances | 2019 |\n|  | consumption in | https://www.iea.org/data-and- |  |\n|  | transport sector (\n\n… [+1027 more chars]",
  "content_hash": "98ac66d8c07d315bfad314f892ad7617f82f105d5a4a2eb295df555b1740ab1d",
  "token_count": 489,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "pdf_path": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "parent_chunk_id": "15087c98-5307-58a7-9a32-1fd99e4c23ba",
  "chunk_index": 8,
  "page_number": 8,
  "page_range": [
    8,
    9
  ],
  "created_at": "2026-06-29T10:33:21.836822+00:00",
  "updated_at": "2026-06-29T10:33:21.836822+00:00"
}
```

## Parent · `70450d09-1270-5da2-89e8-a899a76b4afd`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "70450d09-1270-5da2-89e8-a899a76b4afd",
  "document_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "section_heading": "Introduction",
  "chunk_text": "Introduction (cont.)\n\n|  |  | Meat and dairy |  |  | TFC in |  |  | Plastic waste |  |  |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n|  |  |  |  | TFC in transport |  |  |  |  |  |  |\n|  | production |  |  |  | residential |  | generation |  | Sustainable | Sustainable |\n|  |  |  | sector (TJ/ |  |  |  |  |  |  |  |\n| Country | (tonnes/ |  |  |  | sector (TJ/ |  | (tonnes/ |  | Consumption | Consumption |\n|  |  |  | capita) |  |  |  |  |  |  |  |\n|  | capita) |  |  |  | capita) |  | capita) |  | Index | Index Score |\n|  | Value | Index | Value | Index | Value | Index |\n\n… [+3537 more chars]",
  "content_hash": "cdded626519b10065ce2311e95d50214caa97d19eafb1e23be367b1b7332700b",
  "token_count": 1654,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "pdf_path": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "page_range": [
    9,
    10
  ],
  "created_at": "2026-06-29T10:33:21.836822+00:00",
  "updated_at": "2026-06-29T10:33:21.836822+00:00"
}
```

## Child · `ba5a3d97-6871-5743-be63-1c1b59d8a58d`

- vector: dim=3072 · [-0.0201, 0.0028, -0.0132, -0.0060, -0.0224, -0.0740, 0.0210, 0.0243, …]

```json
{
  "chunk_id": "ba5a3d97-6871-5743-be63-1c1b59d8a58d",
  "document_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "section_heading": "Introduction",
  "chunk_text": "|  |  | Meat and dairy |  |  | TFC in |  |  | Plastic waste |  |  |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n|  |  |  |  | TFC in transport |  |  |  |  |  |  |\n|  | production |  |  |  | residential |  | generation |  | Sustainable | Sustainable |\n|  |  |  | sector (TJ/ |  |  |  |  |  |  |  |\n| Country | (tonnes/ |  |  |  | sector (TJ/ |  | (tonnes/ |  | Consumption | Consumption |\n|  |  |  | capita) |  |  |  |  |  |  |  |\n|  | capita) |  |  |  | capita) |  | capita) |  | Index | Index Score |\n|  | Value | Index | Value | Index | Value | Index | Value | Index |  |  |\n\n… [+475 more chars]",
  "content_hash": "c76b072a8ac0a2fda0c935bfd3b436dfc56e80e21776c3709bfdc04e17534d79",
  "token_count": 540,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "pdf_path": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "parent_chunk_id": "70450d09-1270-5da2-89e8-a899a76b4afd",
  "chunk_index": 9,
  "page_number": 9,
  "page_range": [
    9,
    9
  ],
  "created_at": "2026-06-29T10:33:21.836822+00:00",
  "updated_at": "2026-06-29T10:33:21.836822+00:00"
}
```

## Child · `4bda1301-1798-559e-9841-6eed6827899a`

- vector: dim=3072 · [0.0146, -0.0247, -0.0062, 0.0114, -0.0295, -0.0748, 0.0191, 0.0444, …]

```json
{
  "chunk_id": "4bda1301-1798-559e-9841-6eed6827899a",
  "document_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "section_heading": "Introduction",
  "chunk_text": "| 0.77 | 77 |\n| Japan | 0.03 | 0.86 | 0.02 | 0.75 | 0.01 | 0.75 | 0.06 | 0.67 | 0.76 | 76 | | South Africa | 0.06 | 0.72 | 0.01 | 0.86 | 0.01 | 0.89 | 0.09 | 0.52 | 0.75 | 75 |\n| South Korea | 0.05 | 0.76 | 0.03 | 0.66 | 0.02 | 0.67 | 0.04 | 0.79 | 0.72 | 72 |\n| Brazil | 0.14 | 0.26 | 0.02 | 0.82 | 0.01 | 0.99 | 0.06 | 0.68 | 0.69 | 69 |\n| European |  |  |  |  |  |  |  |  |  |  |\n| Union | 0.09 | 0.51 | 0.01 | 0.88 | 0.01 | 0.88 | 0.10 | 0.47 | 0.68 | 68 |\n| Italy | 0.06 | 0.70 | 0.02 | 0.72 | 0.02 | 0.54 | 0.05 | 0.74 | 0.68 | 68 |\n| Saudi Arabia | 0.02 | 0.91 | 0.06 | 0.33 | 0.02 | 0.70 | 0.\n\n… [+384 more chars]",
  "content_hash": "58797cf81800bb2fb3325f3d8f5603dda2b131108cac6edab577accfd3af913f",
  "token_count": 619,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "pdf_path": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "parent_chunk_id": "70450d09-1270-5da2-89e8-a899a76b4afd",
  "chunk_index": 10,
  "page_number": 9,
  "page_range": [
    9,
    9
  ],
  "created_at": "2026-06-29T10:33:21.836822+00:00",
  "updated_at": "2026-06-29T10:33:21.836822+00:00"
}
```

## Child · `2d8d9504-be57-584f-aeb4-e7861bb90b59`

- vector: dim=3072 · [0.0007, -0.0266, -0.0074, 0.0127, -0.0242, -0.0697, 0.0216, 0.0561, …]

```json
{
  "chunk_id": "2d8d9504-be57-584f-aeb4-e7861bb90b59",
  "document_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "section_heading": "Introduction",
  "chunk_text": "| 0.58 | 58 |\n| Russia | 0.07 | 0.63 | 0.03 | 0.68 | 0.04 | 0.00 | 0.04 | 0.79 | 0.52 | 52 | | Australia | 0.19 | 0.00 | 0.06 | 0.32 | 0.02 | 0.65 | 0.04 | 0.79 | 0.44 | 44 |\n| Germany | 0.10 | 0.49 | 0.03 | 0.68 | 0.03 | 0.36 | 0.18 | 0.00 | 0.38 | 38 |\n| Canada | 0.13 | 0.30 | 0.08 | 0.06 | 0.04 | 0.05 | 0.03 | 0.83 | 0.31 | 31 |\n| United States | 0.14 | 0.24 | 0.08 | 0.00 | 0.03 | 0.19 | 0.12 | 0.32 | 0.19 | 19 |",
  "content_hash": "53ce24095e7b24fe149c43bb6ef7b1a7e5ea8a0ea2f38161faf5d212f4c1fd5e",
  "token_count": 265,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "pdf_path": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "parent_chunk_id": "70450d09-1270-5da2-89e8-a899a76b4afd",
  "chunk_index": 11,
  "page_number": 9,
  "page_range": [
    9,
    9
  ],
  "created_at": "2026-06-29T10:33:21.836822+00:00",
  "updated_at": "2026-06-29T10:33:21.836822+00:00"
}
```

## Child · `1304ceae-5142-59e9-a22b-f0e06c17e660`

- vector: dim=3072 · [-0.0169, 0.0142, -0.0050, 0.0043, -0.0210, -0.0598, 0.0044, 0.0081, …]

```json
{
  "chunk_id": "1304ceae-5142-59e9-a22b-f0e06c17e660",
  "document_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "section_heading": "Introduction",
  "chunk_text": "0.31 | 31 |\n| United States | 0.14 | 0.24 | 0.08 | 0.00 | 0.03 | 0.19 | 0.12 | 0.32 | 0.19 | 19 | 10\t\nSDG Charter Policy Brief\nAmong G20 entities, India has the highest score in the Lifestyles and Consumption Index, while United States \nhas the lowest score. Annexure 1 presents the sub-indices on lifestyles and consumption for G20 countries \nand the EU. India has the highest score—and thus the lowest consumption—for all the four consumption \nsectors (food consumption, transport, residential sector, and plastic waste generation). These score do not \nindicate the normative direction of lifestyle\n\n… [+1316 more chars]",
  "content_hash": "c1f816339467787fedacf8e809867700f237bf81ca21788cf4080b40dde5be56",
  "token_count": 406,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "pdf_path": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "parent_chunk_id": "70450d09-1270-5da2-89e8-a899a76b4afd",
  "chunk_index": 12,
  "page_number": 10,
  "page_range": [
    10,
    10
  ],
  "created_at": "2026-06-29T10:33:21.836822+00:00",
  "updated_at": "2026-06-29T10:33:21.836822+00:00"
}
```

## Parent · `916dc6c3-608a-53c6-829d-7e704326428f`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "916dc6c3-608a-53c6-829d-7e704326428f",
  "document_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "section_heading": "Introduction",
  "chunk_text": "Introduction (cont.)\n\nInternationalizing Lifestyles for Environment: Messages for G20\t\n11\nINSTRUMENTS TO NUDGE LIFESTYLES AND \nCONSUMPTION \nThree categories of instruments become important when it comes to nudging lifestyles and sustainable \nconsumption. These include policy instruments, market instruments and social instruments; these three \ncategories are not mutually exclusive. For example, policy instruments may be vital to introduce market \ninstruments, such as pricing and procurement. Similarly, consumers’ movements and social movements \nfuelled by social instruments may be vital to brin\n\n… [+5273 more chars]",
  "content_hash": "d9761da2f37c341ad33b6da53b262a17f47848cce6c01e3c6c29167a5c269369",
  "token_count": 1305,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "pdf_path": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "page_range": [
    11,
    12
  ],
  "created_at": "2026-06-29T10:33:21.836822+00:00",
  "updated_at": "2026-06-29T10:33:21.836822+00:00"
}
```

## Child · `2b222c9d-8ff9-55b7-a125-8688c3f5ea4a`

- vector: dim=3072 · [-0.0277, -0.0135, -0.0113, -0.0128, -0.0265, 0.0112, -0.0237, 0.0002, …]

```json
{
  "chunk_id": "2b222c9d-8ff9-55b7-a125-8688c3f5ea4a",
  "document_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "section_heading": "Introduction",
  "chunk_text": "Internationalizing Lifestyles for Environment: Messages for G20\t\n11\nINSTRUMENTS TO NUDGE LIFESTYLES AND \nCONSUMPTION \nThree categories of instruments become important when it comes to nudging lifestyles and sustainable \nconsumption. These include policy instruments, market instruments and social instruments; these three \ncategories are not mutually exclusive. For example, policy instruments may be vital to introduce market \ninstruments, such as pricing and procurement. Similarly, consumers’ movements and social movements \nfuelled by social instruments may be vital to bring about changes in pol\n\n… [+1789 more chars]",
  "content_hash": "c5eb8f8cbd25a3397db8d591f5b3911dece0dd1a0b3100d50cd670e2ac79f365",
  "token_count": 443,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "pdf_path": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "parent_chunk_id": "916dc6c3-608a-53c6-829d-7e704326428f",
  "chunk_index": 13,
  "page_number": 11,
  "page_range": [
    11,
    11
  ],
  "created_at": "2026-06-29T10:33:21.836822+00:00",
  "updated_at": "2026-06-29T10:33:21.836822+00:00"
}
```

## Child · `59fc7588-0b88-5d15-8d5e-6be9eec6603a`

- vector: dim=3072 · [-0.0219, -0.0023, -0.0081, 0.0080, -0.0329, -0.0086, -0.0015, 0.0020, …]

```json
{
  "chunk_id": "59fc7588-0b88-5d15-8d5e-6be9eec6603a",
  "document_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "section_heading": "Introduction",
  "chunk_text": "India, European Union, Germany, France and United States have taken steps towards the ‘right to repair’.\n\n12\t\nSDG Charter Policy Brief\nSocial instruments: Social Instruments aim at awareness generation and capacity building of consumers \nthrough providing information about a product or a service, such as product qualities and certifications, to \ninfluence consumer behaviour. Social instruments also include self-regulating and bottom-up instruments \nat the individual and community levels, like carpooling.\nTable 2 depicts instruments for nudging lifestyles and sustainable consumption for the fou\n\n… [+1368 more chars]",
  "content_hash": "a41420291282114cfead6db776cd31c10f43ac86f397bfe567f60f611aac6cee",
  "token_count": 469,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "pdf_path": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "parent_chunk_id": "916dc6c3-608a-53c6-829d-7e704326428f",
  "chunk_index": 14,
  "page_number": 11,
  "page_range": [
    11,
    12
  ],
  "created_at": "2026-06-29T10:33:21.836822+00:00",
  "updated_at": "2026-06-29T10:33:21.836822+00:00"
}
```

## Child · `2fec014e-9a87-5a3e-8818-3e0cce5e5ef9`

- vector: dim=3072 · [-0.0127, -0.0144, -0.0121, 0.0028, -0.0181, -0.0235, 0.0105, 0.0031, …]

```json
{
  "chunk_id": "2fec014e-9a87-5a3e-8818-3e0cce5e5ef9",
  "document_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "section_heading": "Introduction",
  "chunk_text": "items\n\t»\nSubsidies on food products with low \nemissions and environmental impacts\n\t»\nWithdrawing \ninappropriate \nproducts\n\t»\nUse of contracts and \nconditions to shape \nsupply chains\n\t»\nConsumer reward \nschemes\n\t»\nFocused marketing on only healthy and \nsustainably produced \nfoods\n\t»\nLabelling*\n\t»\nBuild cultural \nappeal for \nhealthy diets, \norganic \nfood, from \nsustainable food \nsystems\n\t»\nLegislative \nchange \ncampaigns\n\t»\nCampaigns \nfor alternative \nproducts\nResidential \nBuildings\n\t»\nAppliance standards*\n\t»\nBuilding codes*\n\t»\nMandatory audits\n\t»\nUtility demand side management*\n\t»\nMandatory labe\n\n… [+1153 more chars]",
  "content_hash": "4126db881d9a0ae6a22fd2aac65a28aec44649d58f37d413b41045bf3522d9cd",
  "token_count": 454,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "pdf_path": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "parent_chunk_id": "916dc6c3-608a-53c6-829d-7e704326428f",
  "chunk_index": 15,
  "page_number": 12,
  "page_range": [
    12,
    12
  ],
  "created_at": "2026-06-29T10:33:21.836822+00:00",
  "updated_at": "2026-06-29T10:33:21.836822+00:00"
}
```

## Parent · `12e9896e-305f-5f91-b0fb-a5a3b8dc2856`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "12e9896e-305f-5f91-b0fb-a5a3b8dc2856",
  "document_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "section_heading": "Introduction",
  "chunk_text": "Introduction (cont.)\n\nInternationalizing Lifestyles for Environment: Messages for G20\t\n13\nPolicy Instruments\nMarket Instruments\nSocial instruments \nWaste \nDisposal\n\t»\nRight to repair\n\t»\nProduct restrictions or bans\n\t»\nStandards for recycled materials\n\t»\nBans/restrictions on landfill\n\t»\nTax benefits for recycled materials\n\t»\nLandfill and incineration taxes\n\t»\nProgrammatic interventions*\n\t»\nDeposit Refund \nSchemes\n\t»\nPay-as-you throw \npricing for waste \ncollection system\n\t»\nSoft loans to \nconstruct waste \nsegregation & \nprocessing facilities\n\t»\nLabelling and \ncertification \nschemes*\n\t»\nTake back\n\n… [+9013 more chars]",
  "content_hash": "4c2da3a4e4e0bdeed851a18a923c6d110d27d218d411e5a5341a9874992ad1dc",
  "token_count": 1948,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "pdf_path": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "page_range": [
    13,
    14
  ],
  "created_at": "2026-06-29T10:33:21.836822+00:00",
  "updated_at": "2026-06-29T10:33:21.836822+00:00"
}
```

## Child · `6aa17441-1d3d-5a08-b629-632c82873497`

- vector: dim=3072 · [-0.0373, 0.0100, -0.0068, -0.0055, -0.0220, -0.0146, -0.0017, -0.0048, …]

```json
{
  "chunk_id": "6aa17441-1d3d-5a08-b629-632c82873497",
  "document_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "section_heading": "Introduction",
  "chunk_text": "Internationalizing Lifestyles for Environment: Messages for G20\t\n13\nPolicy Instruments\nMarket Instruments\nSocial instruments \nWaste \nDisposal\n\t»\nRight to repair\n\t»\nProduct restrictions or bans\n\t»\nStandards for recycled materials\n\t»\nBans/restrictions on landfill\n\t»\nTax benefits for recycled materials\n\t»\nLandfill and incineration taxes\n\t»\nProgrammatic interventions*\n\t»\nDeposit Refund \nSchemes\n\t»\nPay-as-you throw \npricing for waste \ncollection system\n\t»\nSoft loans to \nconstruct waste \nsegregation & \nprocessing facilities\n\t»\nLabelling and \ncertification \nschemes*\n\t»\nTake back/ buy-\nback schemes/ \n\n\n… [+1479 more chars]",
  "content_hash": "f97e9893175dd5dd44fe2e032d074868b45bbacc87ec838c2f060d0131b204b5",
  "token_count": 438,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "pdf_path": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "parent_chunk_id": "12e9896e-305f-5f91-b0fb-a5a3b8dc2856",
  "chunk_index": 16,
  "page_number": 13,
  "page_range": [
    13,
    13
  ],
  "created_at": "2026-06-29T10:33:21.836822+00:00",
  "updated_at": "2026-06-29T10:33:21.836822+00:00"
}
```

## Child · `a54db484-66a2-5d99-8f6d-754252847a80`

- vector: dim=3072 · [-0.0289, 0.0209, -0.0119, -0.0150, -0.0153, -0.0242, 0.0074, -0.0236, …]

```json
{
  "chunk_id": "a54db484-66a2-5d99-8f6d-754252847a80",
  "document_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "section_heading": "Introduction",
  "chunk_text": "Another way to promote better consumer choices and lifestyles \nis through the social instrument of raising awareness about the health benefits that using active transports (like walking and cycling) brings (Egset & Nordfjœrn, 2019). There is scope to deploy more instruments, \nespecially when it comes to market instruments and social instruments, in the transport sector.\nIn the food sector, for G20, most policies have focused on food safety and to some extent on labelling. \nThis is also because for many developing countries, ensuring food availability has been a focus along with \nminimizing was\n\n… [+1527 more chars]",
  "content_hash": "08dc1f5cba5828f1b94a34acea70d307bd9b8744491904385e5a14999cbf99c8",
  "token_count": 387,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "pdf_path": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "parent_chunk_id": "12e9896e-305f-5f91-b0fb-a5a3b8dc2856",
  "chunk_index": 17,
  "page_number": 13,
  "page_range": [
    13,
    13
  ],
  "created_at": "2026-06-29T10:33:21.836822+00:00",
  "updated_at": "2026-06-29T10:33:21.836822+00:00"
}
```

## Child · `09239c07-ff44-5688-8ccf-b0b4eacb1eec`

- vector: dim=3072 · [-0.0328, 0.0001, -0.0043, -0.0116, -0.0142, -0.0331, 0.0282, 0.0048, …]

```json
{
  "chunk_id": "09239c07-ff44-5688-8ccf-b0b4eacb1eec",
  "document_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "section_heading": "Introduction",
  "chunk_text": "The G20 Energy Efficiency Leading Programme \n(EELP) in collaboration with the International Energy Partnership for Energy Efficiency Collaboration (IPEEC) |  | » | Take back/ buy- |\n| --- | --- | --- |\n|  |  | back schemes/ |\n|  |  | Extended producer |\n|  |  | responsibility* |\n| *Instruments that are being considered in G20 countries |  |  |\n|  | In the transport sector, most of the G20 countries have used the policy instruments pertaining to fuel efficiency |  |\n|  | and emissions, along with investment in public infrastructure. Brazil uses registration taxes on vehicles |  |\n|  | based on \n\n… [+2045 more chars]",
  "content_hash": "fca3a0bda18f8d9257d38ba52837220a305a5ef630ae749e879babc71c4c52f5",
  "token_count": 580,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "pdf_path": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "parent_chunk_id": "12e9896e-305f-5f91-b0fb-a5a3b8dc2856",
  "chunk_index": 18,
  "page_number": 13,
  "page_range": [
    13,
    13
  ],
  "created_at": "2026-06-29T10:33:21.836822+00:00",
  "updated_at": "2026-06-29T10:33:21.836822+00:00"
}
```

## Child · `c83d6543-4131-5b21-904e-e4ed653b9a14`

- vector: dim=3072 · [-0.0196, 0.0022, -0.0083, -0.0036, -0.0018, -0.0327, 0.0232, -0.0119, …]

```json
{
  "chunk_id": "c83d6543-4131-5b21-904e-e4ed653b9a14",
  "document_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "section_heading": "Introduction",
  "chunk_text": "Market instruments can play |  |\n|  | an important role in pricing, communication, production and distribution of environmentally sustainable |  |\n|  | and healthy food products. Communicating aspects like – the production form, origin, materials used, |  | |  | transport, impact on the environment, packaging used and possible waste that will be generated – may help |  |\n|  | consumers in making informed choices on food and promote sustainable food consumption. Corporate |  |\n|  | financiers, traders, processors, brands and retailers that make up the global supply chains must support |  |\n| th\n\n… [+884 more chars]",
  "content_hash": "6a057ae8b681eedd0708b0b028a3157e34b8631a6d16288bd42a8f467d929815",
  "token_count": 301,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "pdf_path": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "parent_chunk_id": "12e9896e-305f-5f91-b0fb-a5a3b8dc2856",
  "chunk_index": 19,
  "page_number": 13,
  "page_range": [
    13,
    13
  ],
  "created_at": "2026-06-29T10:33:21.836822+00:00",
  "updated_at": "2026-06-29T10:33:21.836822+00:00"
}
```

## Child · `a0f6a8f3-7e28-5d03-9abc-26c89b98e328`

- vector: dim=3072 · [-0.0257, 0.0129, -0.0097, -0.0214, -0.0249, -0.0046, 0.0350, 0.0071, …]

```json
{
  "chunk_id": "a0f6a8f3-7e28-5d03-9abc-26c89b98e328",
  "document_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "section_heading": "Introduction",
  "chunk_text": "The G20 Energy Efficiency Leading Programme |  |  |\n| (EELP) in collaboration with the International Energy Partnership for Energy Efficiency Collaboration (IPEEC) |  |  | 14\t\nSDG Charter Policy Brief\nfocuses on promoting energy efficiency through research, information dissemination, policy options and \ndesigning and strengthening the development and implementation frameworks. While there has been a \nheavy focus on energy, considerable gaps exist in the residential building sector on water conservation – \nwhen it comes to deploying large scale interventions. Moreover, many interventions are fo\n\n… [+1406 more chars]",
  "content_hash": "de42a299425215019ff30f522ccd68d733710272ab12cb4c45bc75a9adfd58ea",
  "token_count": 383,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "pdf_path": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "parent_chunk_id": "12e9896e-305f-5f91-b0fb-a5a3b8dc2856",
  "chunk_index": 20,
  "page_number": 14,
  "page_range": [
    14,
    14
  ],
  "created_at": "2026-06-29T10:33:21.836822+00:00",
  "updated_at": "2026-06-29T10:33:21.836822+00:00"
}
```

## Parent · `49a3d29f-b4fc-5267-b32d-5e2f6eb3eec4`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "49a3d29f-b4fc-5267-b32d-5e2f6eb3eec4",
  "document_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "section_heading": "Introduction",
  "chunk_text": "Introduction (cont.)\n\nInternationalizing Lifestyles for Environment: Messages for G20\t\n15\nWAY FORWARD: INTERNATIONALIZING LIFESTYLES \nAND DEPLOYING INSTRUMENTS\nThe messages from our stakeholder dialogue point to the need for nudging consumer behaviour by a variety \nof stakeholders. The recommendations from the study as well as the stakeholder consultations (TERI, 2022) \nare summarized below.\n\t»\nInternationalizing lifestyles and promoting normative shifts through G20: A critical mass is needed \nfor norms and institutions to change. There is need for a global campaign that can be supported by \na\n\n… [+7401 more chars]",
  "content_hash": "23104282eac777a587c56b503d4bb3f042f26f38d71ccbaa0e4018e4cd8e93a2",
  "token_count": 1625,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "pdf_path": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "page_range": [
    15,
    17
  ],
  "created_at": "2026-06-29T10:33:21.836822+00:00",
  "updated_at": "2026-06-29T10:33:21.836822+00:00"
}
```

## Child · `3e52c124-2b31-51d9-bf82-1f130a623614`

- vector: dim=3072 · [-0.0403, -0.0208, -0.0187, -0.0157, -0.0125, -0.0088, 0.0004, 0.0083, …]

```json
{
  "chunk_id": "3e52c124-2b31-51d9-bf82-1f130a623614",
  "document_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "section_heading": "Introduction",
  "chunk_text": "Internationalizing Lifestyles for Environment: Messages for G20\t\n15\nWAY FORWARD: INTERNATIONALIZING LIFESTYLES \nAND DEPLOYING INSTRUMENTS\nThe messages from our stakeholder dialogue point to the need for nudging consumer behaviour by a variety \nof stakeholders. The recommendations from the study as well as the stakeholder consultations (TERI, 2022) \nare summarized below.\n\t»\nInternationalizing lifestyles and promoting normative shifts through G20: A critical mass is needed \nfor norms and institutions to change. There is need for a global campaign that can be supported by \nall relevant actors, at\n\n… [+1220 more chars]",
  "content_hash": "a77a4216296f370e619d7fb52e5e0bdc6002bf876e76e8479532da01563f44be",
  "token_count": 413,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "pdf_path": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "parent_chunk_id": "49a3d29f-b4fc-5267-b32d-5e2f6eb3eec4",
  "chunk_index": 21,
  "page_number": 15,
  "page_range": [
    15,
    15
  ],
  "created_at": "2026-06-29T10:33:21.836822+00:00",
  "updated_at": "2026-06-29T10:33:21.836822+00:00"
}
```

## Child · `cafbee95-2176-5b00-87d3-24f50db54b42`

- vector: dim=3072 · [-0.0263, -0.0093, -0.0197, -0.0159, -0.0033, -0.0085, 0.0034, 0.0130, …]

```json
{
  "chunk_id": "cafbee95-2176-5b00-87d3-24f50db54b42",
  "document_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "section_heading": "Introduction",
  "chunk_text": "s and \ninstruments such as \nspending on public \nawareness\n\t»\nInclude mandate \non sustainable \nlifestyles\n\t»\nSecretary General \nReport on lifestyles, \nalong with UN \nagencies such as \n10YFP/ One Planet \nNetwork and UNEP | The messages from our stakeholder dialogue point to the need for nudging consumer behaviour by a variety |  |\n| --- | --- |\n| of stakeholders. The recommendations from the study as well as the stakeholder consultations (TERI, 2022) |  |\n| are summarized below. |  |\n| » | Internationalizing lifestyles and promoting normative shifts through G20: A critical mass is needed |\n|  | \n\n… [+848 more chars]",
  "content_hash": "9379f7bbd975d0cfa6aa0760d6e85ec11d0984fc35a019151df7b69167502940",
  "token_count": 321,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "pdf_path": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "parent_chunk_id": "49a3d29f-b4fc-5267-b32d-5e2f6eb3eec4",
  "chunk_index": 22,
  "page_number": 15,
  "page_range": [
    15,
    15
  ],
  "created_at": "2026-06-29T10:33:21.836822+00:00",
  "updated_at": "2026-06-29T10:33:21.836822+00:00"
}
```

## Child · `82a702cf-b49b-5abf-8eaf-d629e25894c6`

- vector: dim=3072 · [-0.0257, -0.0019, -0.0152, -0.0149, -0.0098, -0.0085, 0.0031, -0.0063, …]

```json
{
  "chunk_id": "82a702cf-b49b-5abf-8eaf-d629e25894c6",
  "document_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "section_heading": "Introduction",
  "chunk_text": "Lifestyles could also be considered as a theme for the High-level Political Forum - Sustainable |\n|  | Development Goals. Table 3 presents key hooks for internationalizing lifestyle for environment. | 16\t\nSDG Charter Policy Brief\n\t»\nStrengthening global indicator frameworks: SDG 12 indicators can include/have more downstream \nindicators – especially, when it comes to consumers and individuals – along with instruments such as \neco-labels. This will be an important step forward when it comes to internationalizing lifestyles.\n\t»\nPromoting adaptation and mitigation behaviours: From a Global South \n\n… [+1870 more chars]",
  "content_hash": "89c11f1fd189c99bd39de85209af0bb802b83a27e367bced658fa202bfc629cb",
  "token_count": 477,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "pdf_path": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "parent_chunk_id": "49a3d29f-b4fc-5267-b32d-5e2f6eb3eec4",
  "chunk_index": 23,
  "page_number": 16,
  "page_range": [
    16,
    16
  ],
  "created_at": "2026-06-29T10:33:21.836822+00:00",
  "updated_at": "2026-06-29T10:33:21.836822+00:00"
}
```

## Child · `b38087cc-5799-5d16-a0ae-38304775fdf0`

- vector: dim=3072 · [-0.0460, -0.0167, -0.0090, -0.0010, -0.0301, -0.0127, 0.0017, -0.0179, …]

```json
{
  "chunk_id": "b38087cc-5799-5d16-a0ae-38304775fdf0",
  "document_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "section_heading": "Introduction",
  "chunk_text": "Consumers need services \nrather than the products, which implies that policies should aim at providing well-functioning and \naccessible public services, along with enabling conditions for the market. For example, for mobility, \npolicy instruments may be accompanied by certain business models, such as ride sharing. Internationalizing Lifestyles for Environment: Messages for G20\t\n17\n\t»\nConsideration of pricing and retrofitting: It is important to look at the aspect of pricing as masses \nmay not be able to afford expensive goods and services. In the mobility section, we are talking about \nscrappa\n\n… [+2372 more chars]",
  "content_hash": "b8db68dd6f7392b8ff299b63e9f5b8f1fa95409a4e382cdaae524c2dd6f6f35d",
  "token_count": 565,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "pdf_path": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "parent_chunk_id": "49a3d29f-b4fc-5267-b32d-5e2f6eb3eec4",
  "chunk_index": 24,
  "page_number": 17,
  "page_range": [
    17,
    17
  ],
  "created_at": "2026-06-29T10:33:21.836822+00:00",
  "updated_at": "2026-06-29T10:33:21.836822+00:00"
}
```

## Parent · `144834ae-0bb4-5adb-80b5-466df21a1cd4`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "144834ae-0bb4-5adb-80b5-466df21a1cd4",
  "document_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "section_heading": "Introduction",
  "chunk_text": "Introduction (cont.)\n\n18\t\nSDG Charter Policy Brief\nREFERENCES\nAl-Fouzan, S. A. (2012). Using car parking requirements to promote sustainable transport development in the Kingdom \nof Saudi Arabia. Cities. 29(3), 201-211.\nEgset, K. S., & Nordfjœrn, T. (2019). The role of transport priorities, transport attitudes and situational factors for sustainable \ntransport mode use in wintertime. Transportation Research Part F: Traffic Psychology and Behaviour. 62, 473-482. \nFAO (Food and Agriculture Organization). (2022). Meat Production in Our World in Data, URL: https://ourworldindata.\norg/meat-producti\n\n… [+3824 more chars]",
  "content_hash": "f97487ab4db2bdb4cdc2bc6e87dfc4e47a9179c38e026bbf695e572bf529c80c",
  "token_count": 1104,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "pdf_path": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "page_range": [
    18,
    20
  ],
  "created_at": "2026-06-29T10:33:21.836822+00:00",
  "updated_at": "2026-06-29T10:33:21.836822+00:00"
}
```

## Child · `ed3cad3c-3255-5a49-88dc-0cc885a6a167`

- vector: dim=3072 · [0.0026, 0.0403, -0.0110, 0.0067, -0.0045, -0.0023, -0.0033, 0.0073, …]

```json
{
  "chunk_id": "ed3cad3c-3255-5a49-88dc-0cc885a6a167",
  "document_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "section_heading": "Introduction",
  "chunk_text": "18\t\nSDG Charter Policy Brief\nREFERENCES\nAl-Fouzan, S. A. (2012). Using car parking requirements to promote sustainable transport development in the Kingdom \nof Saudi Arabia. Cities. 29(3), 201-211.\nEgset, K. S., & Nordfjœrn, T. (2019). The role of transport priorities, transport attitudes and situational factors for sustainable \ntransport mode use in wintertime. Transportation Research Part F: Traffic Psychology and Behaviour. 62, 473-482. \nFAO (Food and Agriculture Organization). (2022). Meat Production in Our World in Data, URL: https://ourworldindata.\norg/meat-production (Last accessed on 2\n\n… [+990 more chars]",
  "content_hash": "ae51733868271805406a196f86c7c21c0e06265fa8cb15e6a6471b6225e80043",
  "token_count": 445,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "pdf_path": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "parent_chunk_id": "144834ae-0bb4-5adb-80b5-466df21a1cd4",
  "chunk_index": 25,
  "page_number": 18,
  "page_range": [
    18,
    18
  ],
  "created_at": "2026-06-29T10:33:21.836822+00:00",
  "updated_at": "2026-06-29T10:33:21.836822+00:00"
}
```

## Child · `8821a9c0-be6c-592d-aaa6-68b359b726d1`

- vector: dim=3072 · [-0.0321, 0.0114, -0.0073, -0.0011, -0.0175, -0.0136, 0.0087, 0.0152, …]

```json
{
  "chunk_id": "8821a9c0-be6c-592d-aaa6-68b359b726d1",
  "document_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "section_heading": "Introduction",
  "section_type": "references",
  "chunk_text": "Hasija, G. Lisboa, S. Luz, J. Malley, (eds.)]. Cambridge University Press, \nCambridge, UK and New York, NY, USA. doi: 10.1017/9781009157926.001. Jambeck et al. (2015). Plastic waste inputs from land into the ocean. Science. 347(6223), 768-771 in Our World in Data. \nURL: https://ourworldindata.org/grapher/plastic-waste-generation-total (Last accessed on 25 October 2022).\nMEA (Ministry of External Affairs). (2022). India’s Forthcoming G20 Presidency. New Delhi: MEA. URL: https://www.mea.\ngov.in/press-releases.htm?dtl/35700/Indias_forthcoming_G20_Presidency (Last Accessed 25 October 2022).\nNITI A\n\n… [+479 more chars]",
  "content_hash": "366b7274a2cea9b99a8801b85c85243b8abcce2204f38cba23987f53e498ad40",
  "token_count": 303,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "pdf_path": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "parent_chunk_id": "144834ae-0bb4-5adb-80b5-466df21a1cd4",
  "chunk_index": 26,
  "page_number": 18,
  "page_range": [
    18,
    18
  ],
  "created_at": "2026-06-29T10:33:21.836822+00:00",
  "updated_at": "2026-06-29T10:33:21.836822+00:00"
}
```

## Child · `a0e04f67-1e36-572c-9d9f-5156d9b47e15`

- vector: dim=3072 · [0.0120, 0.0297, -0.0153, 0.0082, -0.0172, 0.0148, 0.0354, 0.0170, …]

```json
{
  "chunk_id": "a0e04f67-1e36-572c-9d9f-5156d9b47e15",
  "document_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "section_heading": "Introduction",
  "chunk_text": "Act4Earth and World Sustainable Development Summit. New Delhi: The \nEnergy and Resources Institute.\nUNEP (United Nations Environment Programme). (2022). Global Strategy for Sustainable Consumption and Production \n2023-2030. UNEP. 20\t\nSDG Charter Policy Brief\nWORLD SUSTAINABLE \nDEVELOPMENT SUMMIT\nThe World Sustainable Development Summit (WSDS) is the annual \nflagship Track II initiative organized by The Energy and Resources Institute \n(TERI). Instituted in 2001, the Summit series has a legacy of over two \ndecades for making ‘sustainable development’ a globally shared goal. \nThe only independent\n\n… [+1505 more chars]",
  "content_hash": "2aeda2acc3e442e22ed5b1ad6275b4c1bb26c3f3e8ca81555e97b39447892f82",
  "token_count": 456,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "pdf_path": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "parent_chunk_id": "144834ae-0bb4-5adb-80b5-466df21a1cd4",
  "chunk_index": 27,
  "page_number": 20,
  "page_range": [
    20,
    20
  ],
  "created_at": "2026-06-29T10:33:21.836822+00:00",
  "updated_at": "2026-06-29T10:33:21.836822+00:00"
}
```
