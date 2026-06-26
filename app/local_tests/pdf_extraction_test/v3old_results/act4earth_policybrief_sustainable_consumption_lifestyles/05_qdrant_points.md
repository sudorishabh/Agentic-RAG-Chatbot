# Qdrant points — Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf

- points (rows upserted): **33**
- embedded: **True** · model `text-embedding-3-large` · dim 3072

Each point is `{id, vector, payload}` exactly as `index_chunks` upserts it. Children carry their embedding; parents carry a zero vector and are reached through their children. Below, vectors are truncated and `chunk_text` is clipped — see `05_qdrant_points.json` for the full data.

---

## Parent · `ac454453-f8e9-5525-83ff-de3b28637c1b`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "ac454453-f8e9-5525-83ff-de3b28637c1b",
  "document_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "section_heading": "ACT4EARTH — SDG CHARTER POLICY BRIEF — INTERNATIONALIZING — LIFESTYLES FOR — ENVIRONMENT — MESSAGES FOR G20 — ISBN 978-93-94657-10-6 — AUTHORS",
  "chunk_text": "ACT4EARTH — SDG CHARTER POLICY BRIEF — INTERNATIONALIZING — LIFESTYLES FOR — ENVIRONMENT — MESSAGES FOR G20 — ISBN 978-93-94657-10-6 — AUTHORS\n\nShailly Kedia, Shweta Gautam, Manish Anand, Ishan Khetan, Nivedita Cholayil, Saheli Das\nREVIEWER\nProdipto Ghosh, Suneel Pandey\nACKNOWLEDGMENTS\nWe thank Bloomberg Philanthropies [Star Partner], the Rockefeller Foundation [Premier \nPartner], German Federal Ministry for the Environment, Nature Conservation, Nuclear \nSafety and Consumer Protection (BMUV) and International Climate Initiative (IKI) [Senior \nPartner], along with Tata Cleantech Capital Ltd [As\n\n… [+808 more chars]",
  "content_hash": "ea6d8ba00f6f3c068b9a0f0dfeade3b87eb8b4a3c160f26b9621b065a5febf95",
  "token_count": 331,
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
    2,
    2
  ],
  "created_at": "2026-06-25T12:24:51.956129+00:00",
  "updated_at": "2026-06-25T12:24:51.956129+00:00"
}
```

## Child · `4a4870bf-7578-5c1e-b005-08591ee2d306`

- vector: dim=3072 · [-0.0059, 0.0026, -0.0189, -0.0268, -0.0187, -0.0090, -0.0014, 0.0071, …]

```json
{
  "chunk_id": "4a4870bf-7578-5c1e-b005-08591ee2d306",
  "document_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "section_heading": "ACT4EARTH — SDG CHARTER POLICY BRIEF — INTERNATIONALIZING — LIFESTYLES FOR — ENVIRONMENT — MESSAGES FOR G20 — ISBN 978-93-94657-10-6 — AUTHORS",
  "chunk_text": "Shailly Kedia, Shweta Gautam, Manish Anand, Ishan Khetan, Nivedita Cholayil, Saheli Das\nREVIEWER\nProdipto Ghosh, Suneel Pandey\nACKNOWLEDGMENTS\nWe thank Bloomberg Philanthropies [Star Partner], the Rockefeller Foundation [Premier \nPartner], German Federal Ministry for the Environment, Nature Conservation, Nuclear \nSafety and Consumer Protection (BMUV) and International Climate Initiative (IKI) [Senior \nPartner], along with Tata Cleantech Capital Ltd [Associate Partner] for their support for the \nWorld Sustainable Development Summit and Act4Earth. We thank One Planet Network for \npartnering for \n\n… [+664 more chars]",
  "content_hash": "c5de9f16da6dc409cce76962309c62174743de834e4f1d95b1c9781aee3ab28c",
  "token_count": 282,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "pdf_path": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "parent_chunk_id": "ac454453-f8e9-5525-83ff-de3b28637c1b",
  "chunk_index": 0,
  "page_number": 2,
  "page_range": [
    2,
    2
  ],
  "created_at": "2026-06-25T12:24:51.956129+00:00",
  "updated_at": "2026-06-25T12:24:51.956129+00:00"
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
  "created_at": "2026-06-25T12:24:51.956129+00:00",
  "updated_at": "2026-06-25T12:24:51.956129+00:00"
}
```

## Child · `5911f148-fff8-5bee-a4c6-8105782e7901`

- vector: dim=3072 · [-0.0187, -0.0232, -0.0142, -0.0283, -0.0147, -0.0106, 0.0121, 0.0089, …]

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
  "created_at": "2026-06-25T12:24:51.956129+00:00",
  "updated_at": "2026-06-25T12:24:51.956129+00:00"
}
```

## Child · `87815a3f-8947-599d-b9a0-e2eb45b932e7`

- vector: dim=3072 · [-0.0156, 0.0050, -0.0149, -0.0063, -0.0254, -0.0141, 0.0110, 0.0070, …]

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
  "created_at": "2026-06-25T12:24:51.956129+00:00",
  "updated_at": "2026-06-25T12:24:51.956129+00:00"
}
```

## Child · `90c55f49-9bb2-536f-ad89-4dfa1cb1d1be`

- vector: dim=3072 · [-0.0310, 0.0143, -0.0171, 0.0038, -0.0253, -0.0357, 0.0094, -0.0232, …]

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
  "created_at": "2026-06-25T12:24:51.956129+00:00",
  "updated_at": "2026-06-25T12:24:51.956129+00:00"
}
```

## Child · `51d0e2a6-ea4c-58d3-9058-9d55901d24a5`

- vector: dim=3072 · [-0.0200, -0.0087, -0.0109, 0.0144, -0.0384, -0.0127, -0.0248, 0.0027, …]

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
  "created_at": "2026-06-25T12:24:51.956129+00:00",
  "updated_at": "2026-06-25T12:24:51.956129+00:00"
}
```

## Child · `5d119d9a-f907-5b22-a8a6-27874acf75a5`

- vector: dim=3072 · [-0.0141, -0.0134, -0.0133, -0.0019, -0.0266, -0.0209, -0.0026, -0.0259, …]

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
  "created_at": "2026-06-25T12:24:51.956129+00:00",
  "updated_at": "2026-06-25T12:24:51.956129+00:00"
}
```

## Parent · `90cf9e88-89e9-5e58-b437-37a0785c3569`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "90cf9e88-89e9-5e58-b437-37a0785c3569",
  "document_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "section_heading": "LIFESTYLES AND CONSUMPTION INDEX FOR G20",
  "chunk_text": "LIFESTYLES AND CONSUMPTION INDEX FOR G20\n\nTo understand the state of lifestyles and consumption for G20 countries and the European Union, a composite\nindex and indices on consumption sectors (such as food, transport, residential and waste management)\nhave been developed. Table 1 summarises the indicators used in calculating the metrics for G20 countries\nand the European Union.\n\n| Sector | Indicator | Data source | Year |\n| --- | --- | --- | --- |\n| Transport | Total final energy consumption in transport sector (TJ/ capita) | IEA World Energy Balances https://www.iea.org/data-and- statistics/da\n\n… [+2655 more chars]",
  "content_hash": "1afdccb981b8d90c765105db4ea501e0f988d1dbf5073c9658e59f29081bf926",
  "token_count": 763,
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
  "created_at": "2026-06-25T12:24:51.956129+00:00",
  "updated_at": "2026-06-25T12:24:51.956129+00:00"
}
```

## Child · `945fd016-eb6d-5d49-bde7-2a839822c112`

- vector: dim=3072 · [-0.0159, 0.0041, -0.0139, -0.0237, -0.0165, -0.0651, 0.0119, -0.0075, …]

```json
{
  "chunk_id": "945fd016-eb6d-5d49-bde7-2a839822c112",
  "document_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "section_heading": "LIFESTYLES AND CONSUMPTION INDEX FOR G20",
  "chunk_text": "To understand the state of lifestyles and consumption for G20 countries and the European Union, a composite\nindex and indices on consumption sectors (such as food, transport, residential and waste management)\nhave been developed. Table 1 summarises the indicators used in calculating the metrics for G20 countries\nand the European Union.\n\n| Sector | Indicator | Data source | Year |\n| --- | --- | --- | --- |\n| Transport | Total final energy consumption in transport sector (TJ/ capita) | IEA World Energy Balances https://www.iea.org/data-and- statistics/data-product/world- energy-statistics-and-ba\n\n… [+1345 more chars]",
  "content_hash": "d17b2c571e8ff451a8ef7e49ea2b090eb2d412c1ca8b5328c6eb60d548ca7b39",
  "token_count": 441,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "pdf_path": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "parent_chunk_id": "90cf9e88-89e9-5e58-b437-37a0785c3569",
  "chunk_index": 6,
  "page_number": 8,
  "page_range": [
    8,
    8
  ],
  "created_at": "2026-06-25T12:24:51.956129+00:00",
  "updated_at": "2026-06-25T12:24:51.956129+00:00"
}
```

## Child · `fbbf2ad2-43e4-5c7f-8a61-04a1853a00e4`

- vector: dim=3072 · [-0.0274, 0.0104, -0.0053, -0.0180, -0.0033, -0.0986, 0.0212, -0.0013, …]

```json
{
  "chunk_id": "fbbf2ad2-43e4-5c7f-8a61-04a1853a00e4",
  "document_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "section_heading": "LIFESTYLES AND CONSUMPTION INDEX FOR G20",
  "chunk_text": "food-waste was that the data for all types of food waste\n(households, out-of-home consumption and retail) is not available for all G20 entities - for Turkey, no data\nwas available for food waste; for EU, data was not available for out-of-home consumption category. Further computation and normalization of indicator values is done for identifying and collecting basic data,\nso that it falls in the range of 0-1. This procedure makes the respective values of the chosen indicators (as\nmentioned in the above table) unitless, so that indicators are comparable for construction of an index. In the\nindex\n\n… [+931 more chars]",
  "content_hash": "4bed08b1c7b5c0a8fade51f6a905e2e7e916bb445a4d68887d11dce82cc5d919",
  "token_count": 370,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "pdf_path": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "parent_chunk_id": "90cf9e88-89e9-5e58-b437-37a0785c3569",
  "chunk_index": 7,
  "page_number": 8,
  "page_range": [
    8,
    9
  ],
  "created_at": "2026-06-25T12:24:51.956129+00:00",
  "updated_at": "2026-06-25T12:24:51.956129+00:00"
}
```

## Parent · `1eafa6f0-ce7a-551a-8b7e-79ce15dcc28c`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "1eafa6f0-ce7a-551a-8b7e-79ce15dcc28c",
  "document_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "section_heading": "India — Indonesia — Mexico — China — Turkey — Japan — South Africa — South Korea — Brazil — European Union — Italy — Saudi Arabia — Argentina — United Kingdom — France — Russia — Australia — Germany — Canada — United States",
  "chunk_text": "India — Indonesia — Mexico — China — Turkey — Japan — South Africa — South Korea — Brazil — European Union — Italy — Saudi Arabia — Argentina — United Kingdom — France — Russia — Australia — Germany — Canada — United States\n\n| Country | Meat and dairy production (tonnes/ capita) | Meat and dairy production (tonnes/ capita) | TFC in transport sector (TJ/ capita) | TFC in transport sector (TJ/ capita) | TFC in residential sector (TJ/ capita) | TFC in residential sector (TJ/ capita) | Plastic waste generation (tonnes/ capita) | Plastic waste generation (tonnes/ capita) | Sustainable Consumption I\n\n… [+3701 more chars]",
  "content_hash": "51c7684743af848e1bea0f77f49720d6d7fc8c31a59a05f21597c37156565e25",
  "token_count": 1591,
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
  "created_at": "2026-06-25T12:24:51.956129+00:00",
  "updated_at": "2026-06-25T12:24:51.956129+00:00"
}
```

## Child · `f19d0f2e-5144-5dfc-b157-69c1e4f0dc30`

- vector: dim=3072 · [-0.0150, 0.0040, -0.0127, -0.0100, -0.0279, -0.0702, 0.0283, 0.0112, …]

```json
{
  "chunk_id": "f19d0f2e-5144-5dfc-b157-69c1e4f0dc30",
  "document_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "section_heading": "India — Indonesia — Mexico — China — Turkey — Japan — South Africa — South Korea — Brazil — European Union — Italy — Saudi Arabia — Argentina — United Kingdom — France — Russia — Australia — Germany — Canada — United States",
  "chunk_text": "| Country | Meat and dairy production (tonnes/ capita) | Meat and dairy production (tonnes/ capita) | TFC in transport sector (TJ/ capita) | TFC in transport sector (TJ/ capita) | TFC in residential sector (TJ/ capita) | TFC in residential sector (TJ/ capita) | Plastic waste generation (tonnes/ capita) | Plastic waste generation (tonnes/ capita) | Sustainable Consumption Index | Sustainable Consumption Index Score |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n| Value | Index | Value | Index | Value | Index | Value | Index |  |  |  |\n| India | 0.01 | 1.00 | 0.00 | 1.00 |\n\n… [+606 more chars]",
  "content_hash": "cb2168f409de6a96252429b6f321aad7745d9678cc78cce2dac03a28adddb2d6",
  "token_count": 558,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "pdf_path": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "parent_chunk_id": "1eafa6f0-ce7a-551a-8b7e-79ce15dcc28c",
  "chunk_index": 8,
  "page_number": 9,
  "page_range": [
    9,
    9
  ],
  "created_at": "2026-06-25T12:24:51.956129+00:00",
  "updated_at": "2026-06-25T12:24:51.956129+00:00"
}
```

## Child · `ba5a3d97-6871-5743-be63-1c1b59d8a58d`

- vector: dim=3072 · [-0.0027, -0.0212, -0.0088, 0.0199, -0.0148, -0.0759, 0.0112, 0.0428, …]

```json
{
  "chunk_id": "ba5a3d97-6871-5743-be63-1c1b59d8a58d",
  "document_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "section_heading": "India — Indonesia — Mexico — China — Turkey — Japan — South Africa — South Korea — Brazil — European Union — Italy — Saudi Arabia — Argentina — United Kingdom — France — Russia — Australia — Germany — Canada — United States",
  "chunk_text": "0.75 | 75 |\n| South Korea | 0.05 | 0.76 | 0.03 | 0.66 | 0.02 | 0.67 | 0.04 | 0.79 | 0.72 | 72 | | Brazil | 0.14 | 0.26 | 0.02 | 0.82 | 0.01 | 0.99 | 0.06 | 0.68 | 0.69 | 69 |\n| European Union | 0.09 | 0.51 | 0.01 | 0.88 | 0.01 | 0.88 | 0.10 | 0.47 | 0.68 | 68 |\n| Italy | 0.06 | 0.70 | 0.02 | 0.72 | 0.02 | 0.54 | 0.05 | 0.74 | 0.68 | 68 |\n| Saudi Arabia | 0.02 | 0.91 | 0.06 | 0.33 | 0.02 | 0.70 | 0.06 | 0.70 | 0.66 | 66 |\n| Argentina | 0.13 | 0.29 | 0.02 | 0.83 | 0.01 | 0.78 | 0.07 | 0.64 | 0.63 | 63 |\n| United Kingdom | 0.06 | 0.70 | 0.03 | 0.71 | 0.02 | 0.49 | 0.08 | 0.58 | 0.62 | 62 |\n| Fran\n\n… [+313 more chars]",
  "content_hash": "1f25960d091377f19c32a66d35b5f5937851ca41333c5f039ffedaa561ffa80a",
  "token_count": 572,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "pdf_path": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "parent_chunk_id": "1eafa6f0-ce7a-551a-8b7e-79ce15dcc28c",
  "chunk_index": 9,
  "page_number": 9,
  "page_range": [
    9,
    9
  ],
  "created_at": "2026-06-25T12:24:51.956129+00:00",
  "updated_at": "2026-06-25T12:24:51.956129+00:00"
}
```

## Child · `4bda1301-1798-559e-9841-6eed6827899a`

- vector: dim=3072 · [-0.0024, 0.0098, -0.0119, 0.0031, -0.0363, -0.0441, 0.0049, 0.0370, …]

```json
{
  "chunk_id": "4bda1301-1798-559e-9841-6eed6827899a",
  "document_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "section_heading": "India — Indonesia — Mexico — China — Turkey — Japan — South Africa — South Korea — Brazil — European Union — Italy — Saudi Arabia — Argentina — United Kingdom — France — Russia — Australia — Germany — Canada — United States",
  "chunk_text": "| 0.44 | 44 |\n| Germany | 0.10 | 0.49 | 0.03 | 0.68 | 0.03 | 0.36 | 0.18 | 0.00 | 0.38 | 38 | | Canada | 0.13 | 0.30 | 0.08 | 0.06 | 0.04 | 0.05 | 0.03 | 0.83 | 0.31 | 31 |\n| United States | 0.14 | 0.24 | 0.08 | 0.00 | 0.03 | 0.19 | 0.12 | 0.32 | 0.19 | 19 |\n\nSource: Based on FAO (2022), IEA (2022); and Jambeck et al (2015)",
  "content_hash": "39fe760333a168793be8c3944c64a9d550da849de62185cf8b839bff3f71b18f",
  "token_count": 188,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "pdf_path": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "parent_chunk_id": "1eafa6f0-ce7a-551a-8b7e-79ce15dcc28c",
  "chunk_index": 10,
  "page_number": 9,
  "page_range": [
    9,
    9
  ],
  "created_at": "2026-06-25T12:24:51.956129+00:00",
  "updated_at": "2026-06-25T12:24:51.956129+00:00"
}
```

## Child · `2d8d9504-be57-584f-aeb4-e7861bb90b59`

- vector: dim=3072 · [-0.0235, 0.0103, -0.0067, -0.0032, -0.0280, -0.0558, 0.0049, 0.0061, …]

```json
{
  "chunk_id": "2d8d9504-be57-584f-aeb4-e7861bb90b59",
  "document_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "section_heading": "India — Indonesia — Mexico — China — Turkey — Japan — South Africa — South Korea — Brazil — European Union — Italy — Saudi Arabia — Argentina — United Kingdom — France — Russia — Australia — Germany — Canada — United States",
  "chunk_text": "08 | 0.00 | 0.03 | 0.19 | 0.12 | 0.32 | 0.19 | 19 |\n\nSource: Based on FAO (2022), IEA (2022); and Jambeck et al (2015) 10\t\nSDG Charter Policy Brief\nAmong G20 entities, India has the highest score in the Lifestyles and Consumption Index, while United States \nhas the lowest score. Annexure 1 presents the sub-indices on lifestyles and consumption for G20 countries \nand the EU. India has the highest score—and thus the lowest consumption—for all the four consumption \nsectors (food consumption, transport, residential sector, and plastic waste generation). These score do not \nindicate the normative d\n\n… [+1337 more chars]",
  "content_hash": "6a66a1e6e567019fbd71e32759e55e0066c2248ce9adfb6c15f43ac7b82f6bf1",
  "token_count": 407,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "pdf_path": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "parent_chunk_id": "1eafa6f0-ce7a-551a-8b7e-79ce15dcc28c",
  "chunk_index": 11,
  "page_number": 10,
  "page_range": [
    10,
    10
  ],
  "created_at": "2026-06-25T12:24:51.956129+00:00",
  "updated_at": "2026-06-25T12:24:51.956129+00:00"
}
```

## Parent · `9ccfd484-65fd-59b5-8bd6-c9468467077b`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "9ccfd484-65fd-59b5-8bd6-c9468467077b",
  "document_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "section_heading": "India — Indonesia — Mexico — China — Turkey — Japan — South Africa — South Korea — Brazil — European Union — Italy — Saudi Arabia — Argentina — United Kingdom — France — Russia — Australia — Germany — Canada — United States",
  "chunk_text": "India — Indonesia — Mexico — China — Turkey — Japan — South Africa — South Korea — Brazil — European Union — Italy — Saudi Arabia — Argentina — United Kingdom — France — Russia — Australia — Germany — Canada — United States (cont.)\n\nInternationalizing Lifestyles for Environment: Messages for G20\t\n11\nINSTRUMENTS TO NUDGE LIFESTYLES AND \nCONSUMPTION \nThree categories of instruments become important when it comes to nudging lifestyles and sustainable \nconsumption. These include policy instruments, market instruments and social instruments; these three \ncategories are not mutually exclusive. For e\n\n… [+8731 more chars]",
  "content_hash": "43ad1ec0f2c8b09ee7f947b13a91db1d0eb45e7b8254013ccade89e211e9f5a8",
  "token_count": 1966,
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
    13
  ],
  "created_at": "2026-06-25T12:24:51.956129+00:00",
  "updated_at": "2026-06-25T12:24:51.956129+00:00"
}
```

## Child · `1304ceae-5142-59e9-a22b-f0e06c17e660`

- vector: dim=3072 · [-0.0278, -0.0135, -0.0114, -0.0128, -0.0264, 0.0111, -0.0236, 0.0002, …]

```json
{
  "chunk_id": "1304ceae-5142-59e9-a22b-f0e06c17e660",
  "document_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "section_heading": "India — Indonesia — Mexico — China — Turkey — Japan — South Africa — South Korea — Brazil — European Union — Italy — Saudi Arabia — Argentina — United Kingdom — France — Russia — Australia — Germany — Canada — United States",
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
  "parent_chunk_id": "9ccfd484-65fd-59b5-8bd6-c9468467077b",
  "chunk_index": 12,
  "page_number": 11,
  "page_range": [
    11,
    11
  ],
  "created_at": "2026-06-25T12:24:51.956129+00:00",
  "updated_at": "2026-06-25T12:24:51.956129+00:00"
}
```

## Child · `2b222c9d-8ff9-55b7-a125-8688c3f5ea4a`

- vector: dim=3072 · [-0.0323, -0.0089, -0.0132, 0.0080, -0.0359, 0.0085, -0.0241, 0.0025, …]

```json
{
  "chunk_id": "2b222c9d-8ff9-55b7-a125-8688c3f5ea4a",
  "document_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "section_heading": "India — Indonesia — Mexico — China — Turkey — Japan — South Africa — South Korea — Brazil — European Union — Italy — Saudi Arabia — Argentina — United Kingdom — France — Russia — Australia — Germany — Canada — United States",
  "chunk_text": "India, European Union, Germany, France and United States have taken steps towards the ‘right to repair’.\n\nSocial instruments: Social Instruments aim at awareness generation and capacity building of consumers\nthrough providing information about a product or a service, such as product qualities and certifications, to\ninfluence consumer behaviour. Social instruments also include self-regulating and bottom-up instruments\nat the individual and community levels, like carpooling.\n\nTable 2 depicts instruments for nudging lifestyles and sustainable consumption for the four sectors\nconsidered in the ana\n\n… [+188 more chars]",
  "content_hash": "7612672320b0942d0cc97d0d4f6e0e7a97c3f2eb6e1ac01523e779653e61d3a2",
  "token_count": 153,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "pdf_path": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "parent_chunk_id": "9ccfd484-65fd-59b5-8bd6-c9468467077b",
  "chunk_index": 13,
  "page_number": 11,
  "page_range": [
    11,
    12
  ],
  "created_at": "2026-06-25T12:24:51.956129+00:00",
  "updated_at": "2026-06-25T12:24:51.956129+00:00"
}
```

## Child · `59fc7588-0b88-5d15-8d5e-6be9eec6603a`

- vector: dim=3072 · [-0.0023, -0.0084, -0.0168, -0.0159, -0.0223, -0.0256, 0.0049, 0.0030, …]

```json
{
  "chunk_id": "59fc7588-0b88-5d15-8d5e-6be9eec6603a",
  "document_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "section_heading": "India — Indonesia — Mexico — China — Turkey — Japan — South Africa — South Korea — Brazil — European Union — Italy — Saudi Arabia — Argentina — United Kingdom — France — Russia — Australia — Germany — Canada — United States",
  "chunk_text": "The instruments followed by * denotes the ones that are being deployed in G20\ncountries for the G20 sectors.\n\nTABLE 2: INSTRUMENTS FOR NUDGING LIFESTYLES AND SUSTAINABLE CONSUMPTION |  | Policy Instruments | Policy Instruments |  | Market Instruments | Social instruments |\n| --- | --- | --- | --- | --- | --- |\n| Transport | » | Taxation on fuel and high fuel/emissions vehicles | › | Provision of eco- mobility | » Campaigns on policy measures |\n|  | » | Congestion charges | » | Company logistics | » Advertisements |\n| » | Toll roads |  | and contracts | Public » |  |\n| » > | Government encourag\n\n… [+1796 more chars]",
  "content_hash": "b7d0e0f1837276e3258c3a197e1497045a4d3d95f5a205e6ddfef9b9e05d895a",
  "token_count": 606,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "pdf_path": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "parent_chunk_id": "9ccfd484-65fd-59b5-8bd6-c9468467077b",
  "chunk_index": 14,
  "page_number": 12,
  "page_range": [
    12,
    12
  ],
  "created_at": "2026-06-25T12:24:51.956129+00:00",
  "updated_at": "2026-06-25T12:24:51.956129+00:00"
}
```

## Child · `2fec014e-9a87-5a3e-8818-3e0cce5e5ef9`

- vector: dim=3072 · [-0.0352, -0.0041, -0.0081, -0.0064, -0.0270, -0.0284, 0.0009, 0.0106, …]

```json
{
  "chunk_id": "2fec014e-9a87-5a3e-8818-3e0cce5e5ef9",
  "document_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "section_heading": "India — Indonesia — Mexico — China — Turkey — Japan — South Africa — South Korea — Brazil — European Union — Italy — Saudi Arabia — Argentina — United Kingdom — France — Russia — Australia — Germany — Canada — United States",
  "chunk_text": "elling and certification* | » | Energy efficiency | raising, |\n|  | certificate schemes* | education and |  |  |  |\n| » | Taxes and tax benefits |  | Pricing of water | information |  |\n|  | » |  |  |  |  | | » | Subsidies |  |  | campaigns |  |\n| » | Water harvesting schemes | » | Procurement | » Billing |  |\n|  |  |  |  | disclosure |  |\n|  |  |  |  | programs* |  |\n\n|  | Policy Instruments | Policy Instruments | Market Instruments | Social instruments |\n| --- | --- | --- | --- | --- |\n| Waste | » | Right to repair | » Deposit Refund | » Capacity |\n| Disposal | » | Product restrictions or ba\n\n… [+664 more chars]",
  "content_hash": "0b3e775530987d043d91a9cc54f138c3669d432b3c9cd04c3857da05d59a371b",
  "token_count": 337,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "pdf_path": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "parent_chunk_id": "9ccfd484-65fd-59b5-8bd6-c9468467077b",
  "chunk_index": 15,
  "page_number": 12,
  "page_range": [
    12,
    13
  ],
  "created_at": "2026-06-25T12:24:51.956129+00:00",
  "updated_at": "2026-06-25T12:24:51.956129+00:00"
}
```

## Child · `6aa17441-1d3d-5a08-b629-632c82873497`

- vector: dim=3072 · [-0.0273, 0.0151, -0.0112, -0.0038, -0.0207, -0.0284, -0.0001, -0.0057, …]

```json
{
  "chunk_id": "6aa17441-1d3d-5a08-b629-632c82873497",
  "document_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "section_heading": "India — Indonesia — Mexico — China — Turkey — Japan — South Africa — South Korea — Brazil — European Union — Italy — Saudi Arabia — Argentina — United Kingdom — France — Russia — Australia — Germany — Canada — United States",
  "chunk_text": "|  | » Labelling and certification schemes* |  |  |\n|  |  | » Take back/ buy- back schemes/ |  |  |\n|  |  | Extended producer responsibility* |  |  |\n\n*Instruments that are being considered in G20 countries In the transport sector, most of the G20 countries have used the policy instruments pertaining to fuel efficiency\nand emissions, along with investment in public infrastructure. Brazil uses registration taxes on vehicles\nbased on their engine size and their manufacturer's fleet average efficiency, while the United Kingdom has\nclean air zones where drivers must pay to drive through if their v\n\n… [+1083 more chars]",
  "content_hash": "f6b9d14697a928daf8f116bccc1821bb0c9dc6016fc9851041c906d08907db61",
  "token_count": 334,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "pdf_path": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "parent_chunk_id": "9ccfd484-65fd-59b5-8bd6-c9468467077b",
  "chunk_index": 16,
  "page_number": 13,
  "page_range": [
    13,
    13
  ],
  "created_at": "2026-06-25T12:24:51.956129+00:00",
  "updated_at": "2026-06-25T12:24:51.956129+00:00"
}
```

## Child · `a54db484-66a2-5d99-8f6d-754252847a80`

- vector: dim=3072 · [-0.0219, 0.0150, -0.0146, -0.0050, -0.0157, -0.0533, -0.0003, -0.0241, …]

```json
{
  "chunk_id": "a54db484-66a2-5d99-8f6d-754252847a80",
  "document_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "section_heading": "India — Indonesia — Mexico — China — Turkey — Japan — South Africa — South Korea — Brazil — European Union — Italy — Saudi Arabia — Argentina — United Kingdom — France — Russia — Australia — Germany — Canada — United States",
  "chunk_text": "There is scope to deploy more instruments,\nespecially when it comes to market instruments and social instruments, in the transport sector. In the food sector, for G20, most policies have focused on food safety and to some extent on labelling.\nThis is also because for many developing countries, ensuring food availability has been a focus along with\nminimizing waste in the storage and food distribution segments. Thus, for most countries the focus has\nbeen on production segments of agriculture value chains and on food safety. Market instruments can play\nan important role in pricing, communication\n\n… [+736 more chars]",
  "content_hash": "474f03b7c217fb014f7eae0a55905500eef6e5e3fab64f632c325bea099f89b7",
  "token_count": 238,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "pdf_path": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "parent_chunk_id": "9ccfd484-65fd-59b5-8bd6-c9468467077b",
  "chunk_index": 17,
  "page_number": 13,
  "page_range": [
    13,
    13
  ],
  "created_at": "2026-06-25T12:24:51.956129+00:00",
  "updated_at": "2026-06-25T12:24:51.956129+00:00"
}
```

## Parent · `163a73c8-71a6-58c8-8f05-f8838c52a3f5`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "163a73c8-71a6-58c8-8f05-f8838c52a3f5",
  "document_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "section_heading": "India — Indonesia — Mexico — China — Turkey — Japan — South Africa — South Korea — Brazil — European Union — Italy — Saudi Arabia — Argentina — United Kingdom — France — Russia — Australia — Germany — Canada — United States",
  "chunk_text": "India — Indonesia — Mexico — China — Turkey — Japan — South Africa — South Korea — Brazil — European Union — Italy — Saudi Arabia — Argentina — United Kingdom — France — Russia — Australia — Germany — Canada — United States (cont.)\n\nFor G20 countries, the dominant focus of instruments has been in the categories of standards and labelling\nfor energy-efficient buildings and automatic-networked residential appliances. Thus, for these countries, this\nimplies a higher emphasis on the application and effective implementation of technologies, equipment, and\nappliances at sub-national, national, and i\n\n… [+2010 more chars]",
  "content_hash": "6d50cba14b439dc0ff6b838a0b39b9d6690fbcbaaf3095d7cc6131a3ce3071f5",
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
  "page_range": [
    13,
    14
  ],
  "created_at": "2026-06-25T12:24:51.956129+00:00",
  "updated_at": "2026-06-25T12:24:51.956129+00:00"
}
```

## Child · `09239c07-ff44-5688-8ccf-b0b4eacb1eec`

- vector: dim=3072 · [-0.0234, 0.0187, -0.0081, -0.0114, -0.0228, -0.0045, 0.0251, -0.0052, …]

```json
{
  "chunk_id": "09239c07-ff44-5688-8ccf-b0b4eacb1eec",
  "document_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "section_heading": "India — Indonesia — Mexico — China — Turkey — Japan — South Africa — South Korea — Brazil — European Union — Italy — Saudi Arabia — Argentina — United Kingdom — France — Russia — Australia — Germany — Canada — United States",
  "chunk_text": "For G20 countries, the dominant focus of instruments has been in the categories of standards and labelling\nfor energy-efficient buildings and automatic-networked residential appliances. Thus, for these countries, this\nimplies a higher emphasis on the application and effective implementation of technologies, equipment, and\nappliances at sub-national, national, and international levels. The G20 Energy Efficiency Leading Programme\n(EELP) in collaboration with the International Energy Partnership for Energy Efficiency Collaboration (IPEEC)\n\n14\t\nSDG Charter Policy Brief\nfocuses on promoting energy \n\n… [+1777 more chars]",
  "content_hash": "4cb45c078a91ccc02ae19b81733851fec72ca821c23ae9f1f0c230f8a45a0fa3",
  "token_count": 441,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "pdf_path": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "parent_chunk_id": "163a73c8-71a6-58c8-8f05-f8838c52a3f5",
  "chunk_index": 18,
  "page_number": 13,
  "page_range": [
    13,
    14
  ],
  "created_at": "2026-06-25T12:24:51.956129+00:00",
  "updated_at": "2026-06-25T12:24:51.956129+00:00"
}
```

## Parent · `f04e03b3-947a-5eb7-ab70-15c709c61278`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "f04e03b3-947a-5eb7-ab70-15c709c61278",
  "document_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "section_heading": "WAY FORWARD: INTERNATIONALIZING LIFESTYLES AND DEPLOYING INSTRUMENTS",
  "chunk_text": "WAY FORWARD: INTERNATIONALIZING LIFESTYLES AND DEPLOYING INSTRUMENTS\n\nThe messages from our stakeholder dialogue point to the need for nudging consumer behaviour by a variety\nof stakeholders. The recommendations from the study as well as the stakeholder consultations (TERI, 2022)\nare summarized below.\n\n» Internationalizing lifestyles and promoting normative shifts through G20: A critical mass is needed\nfor norms and institutions to change. There is need for a global campaign that can be supported by\nall relevant actors, at country and global levels, that will help promote understanding on sust\n\n… [+1155 more chars]",
  "content_hash": "26dec010823e4ba5a0654263ea5757173f2771b169003f59abc6b3f781b16f43",
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
  "page_range": [
    15,
    15
  ],
  "created_at": "2026-06-25T12:24:51.956129+00:00",
  "updated_at": "2026-06-25T12:24:51.956129+00:00"
}
```

## Child · `c83d6543-4131-5b21-904e-e4ed653b9a14`

- vector: dim=3072 · [-0.0357, -0.0187, -0.0163, -0.0133, -0.0093, -0.0074, 0.0090, -0.0000, …]

```json
{
  "chunk_id": "c83d6543-4131-5b21-904e-e4ed653b9a14",
  "document_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "section_heading": "WAY FORWARD: INTERNATIONALIZING LIFESTYLES AND DEPLOYING INSTRUMENTS",
  "chunk_text": "The messages from our stakeholder dialogue point to the need for nudging consumer behaviour by a variety\nof stakeholders. The recommendations from the study as well as the stakeholder consultations (TERI, 2022)\nare summarized below.\n\n» Internationalizing lifestyles and promoting normative shifts through G20: A critical mass is needed\nfor norms and institutions to change. There is need for a global campaign that can be supported by\nall relevant actors, at country and global levels, that will help promote understanding on sustainable\nlifestyles. Through G20, India can take a leadership role in i\n\n… [+1085 more chars]",
  "content_hash": "82e0d75f48b97591e5be1fa99b20ee4e104b15d58ee4223eede289224eda8cb1",
  "token_count": 365,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "pdf_path": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "parent_chunk_id": "f04e03b3-947a-5eb7-ab70-15c709c61278",
  "chunk_index": 19,
  "page_number": 15,
  "page_range": [
    15,
    15
  ],
  "created_at": "2026-06-25T12:24:51.956129+00:00",
  "updated_at": "2026-06-25T12:24:51.956129+00:00"
}
```

## Parent · `09cd03a6-f03e-5d2a-b2fb-27aec7720aea`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "09cd03a6-f03e-5d2a-b2fb-27aec7720aea",
  "document_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "section_heading": "G20",
  "chunk_text": "G20\n\n16\t\nSDG Charter Policy Brief\n\t»\nStrengthening global indicator frameworks: SDG 12 indicators can include/have more downstream \nindicators – especially, when it comes to consumers and individuals – along with instruments such as \neco-labels. This will be an important step forward when it comes to internationalizing lifestyles.\n\t»\nPromoting adaptation and mitigation behaviours: From a Global South perspective, when discussing \nlifestyles, climate change adaptation and mitigation need to be considered. Under UNFCCC, the \nSubsidiary Body for Scientific and Technological Advice (SBSTA) can be \n\n… [+8735 more chars]",
  "content_hash": "29c19d07b1c12029cb54c20bbe40684310de0aafa339a91477590ed24f020ea8",
  "token_count": 2049,
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
    16,
    20
  ],
  "created_at": "2026-06-25T12:24:51.956129+00:00",
  "updated_at": "2026-06-25T12:24:51.956129+00:00"
}
```

## Child · `a0f6a8f3-7e28-5d03-9abc-26c89b98e328`

- vector: dim=3072 · [-0.0303, 0.0009, -0.0126, -0.0291, -0.0261, -0.0107, 0.0172, 0.0169, …]

```json
{
  "chunk_id": "a0f6a8f3-7e28-5d03-9abc-26c89b98e328",
  "document_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "section_heading": "G20",
  "chunk_text": "16\t\nSDG Charter Policy Brief\n\t»\nStrengthening global indicator frameworks: SDG 12 indicators can include/have more downstream \nindicators – especially, when it comes to consumers and individuals – along with instruments such as \neco-labels. This will be an important step forward when it comes to internationalizing lifestyles.\n\t»\nPromoting adaptation and mitigation behaviours: From a Global South perspective, when discussing \nlifestyles, climate change adaptation and mitigation need to be considered. Under UNFCCC, the \nSubsidiary Body for Scientific and Technological Advice (SBSTA) can be given\n\n… [+1669 more chars]",
  "content_hash": "30d05c6b282b810e6b8ddffcb94875d615700788ebccb60d109d0bfbdad8a902",
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
  "parent_chunk_id": "09cd03a6-f03e-5d2a-b2fb-27aec7720aea",
  "chunk_index": 20,
  "page_number": 16,
  "page_range": [
    16,
    16
  ],
  "created_at": "2026-06-25T12:24:51.956129+00:00",
  "updated_at": "2026-06-25T12:24:51.956129+00:00"
}
```

## Child · `3e52c124-2b31-51d9-bf82-1f130a623614`

- vector: dim=3072 · [-0.0481, -0.0122, -0.0072, -0.0044, -0.0358, -0.0095, 0.0043, -0.0172, …]

```json
{
  "chunk_id": "3e52c124-2b31-51d9-bf82-1f130a623614",
  "document_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "section_heading": "G20",
  "chunk_text": "Consumers need services \nrather than the products, which implies that policies should aim at providing well-functioning and \naccessible public services, along with enabling conditions for the market. For example, for mobility, \npolicy instruments may be accompanied by certain business models, such as ride sharing. Internationalizing Lifestyles for Environment: Messages for G20\t\n17\n\t»\nConsideration of pricing and retrofitting: It is important to look at the aspect of pricing as masses \nmay not be able to afford expensive goods and services. In the mobility section, we are talking about \nscrappa\n\n… [+1999 more chars]",
  "content_hash": "46efb04472a581280beb1130f567c659ad4f89efca132f6094c84f3afe89bc58",
  "token_count": 498,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "pdf_path": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "parent_chunk_id": "09cd03a6-f03e-5d2a-b2fb-27aec7720aea",
  "chunk_index": 21,
  "page_number": 17,
  "page_range": [
    17,
    17
  ],
  "created_at": "2026-06-25T12:24:51.956129+00:00",
  "updated_at": "2026-06-25T12:24:51.956129+00:00"
}
```

## Child · `cafbee95-2176-5b00-87d3-24f50db54b42`

- vector: dim=3072 · [-0.0165, 0.0256, -0.0096, 0.0045, -0.0136, -0.0110, -0.0152, -0.0003, …]

```json
{
  "chunk_id": "cafbee95-2176-5b00-87d3-24f50db54b42",
  "document_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "section_heading": "G20",
  "chunk_text": "It is essential \nto engage with social movements around community based sustainable consumption, to ensure a diversity of perspectives. More sustainable alternatives should be available and easily accessible, along \nwith providing the enabling conditions to nudge sustainable behaviour. The aspect of trust also becomes \nimportant. Looking at it from the consumer behaviour perspective, it is very important for consumers to \nbe able to trust the information that they get.\n*****\n\n18\t\nSDG Charter Policy Brief\nREFERENCES\nAl-Fouzan, S. A. (2012). Using car parking requirements to promote sustainable \n\n… [+1471 more chars]",
  "content_hash": "112579e2a536c70d6ff4e78bb35eaf45e85e02cf4ecc9d4baefe89759fc69e6b",
  "token_count": 527,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "pdf_path": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "parent_chunk_id": "09cd03a6-f03e-5d2a-b2fb-27aec7720aea",
  "chunk_index": 22,
  "page_number": 17,
  "page_range": [
    17,
    18
  ],
  "created_at": "2026-06-25T12:24:51.956129+00:00",
  "updated_at": "2026-06-25T12:24:51.956129+00:00"
}
```

## Child · `82a702cf-b49b-5abf-8eaf-d629e25894c6`

- vector: dim=3072 · [-0.0321, 0.0115, -0.0073, -0.0011, -0.0174, -0.0136, 0.0087, 0.0152, …]

```json
{
  "chunk_id": "82a702cf-b49b-5abf-8eaf-d629e25894c6",
  "document_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "section_heading": "G20",
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
  "parent_chunk_id": "09cd03a6-f03e-5d2a-b2fb-27aec7720aea",
  "chunk_index": 23,
  "page_number": 18,
  "page_range": [
    18,
    18
  ],
  "created_at": "2026-06-25T12:24:51.956129+00:00",
  "updated_at": "2026-06-25T12:24:51.956129+00:00"
}
```

## Child · `b38087cc-5799-5d16-a0ae-38304775fdf0`

- vector: dim=3072 · [0.0121, 0.0299, -0.0153, 0.0083, -0.0174, 0.0148, 0.0353, 0.0171, …]

```json
{
  "chunk_id": "b38087cc-5799-5d16-a0ae-38304775fdf0",
  "document_id": "act4earth_policybrief_sustainable_consumption_lifestyles_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Act4Earth_PolicyBrief_Sustainable_consumption_Lifestyles.pdf",
  "section_heading": "G20",
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
  "parent_chunk_id": "09cd03a6-f03e-5d2a-b2fb-27aec7720aea",
  "chunk_index": 24,
  "page_number": 20,
  "page_range": [
    20,
    20
  ],
  "created_at": "2026-06-25T12:24:51.956129+00:00",
  "updated_at": "2026-06-25T12:24:51.956129+00:00"
}
```
