# Qdrant points — Navbharat_Times.pdf

- points (rows upserted): **11**
- embedded: **True** · model `text-embedding-3-large` · dim 3072

Each point is `{id, vector, payload}` exactly as `index_chunks` upserts it. Children carry their embedding; parents carry a zero vector and are reached through their children. Below, vectors are truncated and `chunk_text` is clipped — see `05_qdrant_points.json` for the full data.

---

## Parent · `61939316-af73-506c-bd31-ac5cbc64d38f`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "61939316-af73-506c-bd31-ac5cbc64d38f",
  "document_id": "navbharat_times_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Navbharat_Times.pdf",
  "chunk_text": "क्लाइमेट चेंज की भेंट चढ़ेंगी करोड़ों नौकरियां\nमौसम में अप्रत्याशित बदलाव से लोगों को बहुत परेशानी हो रही है। पर्यावरण संकट इस सदी की सबसे बड़ी चुनौती के रूप में हमारे सामने है। ऐसे में सवाल यह भी है कि लोकसभा चुनाव के बाद अगली सरकार के लिए पर्यावरण और अक्षय ऊर्जा कितना बड़ा अजेंडा होगा। ऊर्जा, पर्यावरण और टिकाऊ विकास पर काम करने वाले संस्थान द एनर्जी एंड रिसोर्स इंस्टिट्यूट (TERI) के अपनी स्थापना के 50 साल पूरे करने के मौके पर अरविंद कुमार मिश्रा ने संस्थान की डायरेक्टर जनरल डॉ. विभा धवन से इन तमाम मसलों पर बातचीत की। पेश है बातचीत के अहम अंश :\nदेश में लोकसभा चुनाव की प्रक्रिया शुरू हो गई हैं\n\n… [+2853 more chars]",
  "content_hash": "0ee15c599b5855b6a13a5d850dc8473c6243d12b6634650ad4c2b848e25cac1b",
  "token_count": 3462,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "navbharat_times_pdf",
  "pdf_path": "Navbharat_Times.pdf",
  "page_range": [
    1,
    1
  ],
  "created_at": "2026-06-30T08:33:54.221182+00:00",
  "updated_at": "2026-06-30T08:33:54.221182+00:00"
}
```

## Child · `92a1660e-82b1-5836-b397-0edc2b8f0902`

- vector: dim=3072 · [-0.0129, -0.0281, -0.0048, -0.0124, -0.0065, -0.0042, -0.0111, 0.0286, …]

```json
{
  "chunk_id": "92a1660e-82b1-5836-b397-0edc2b8f0902",
  "document_id": "navbharat_times_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Navbharat_Times.pdf",
  "chunk_text": "क्लाइमेट चेंज की भेंट चढ़ेंगी करोड़ों नौकरियां\n\nमौसम में अप्रत्याशित बदलाव से लोगों को बहुत परेशानी हो रही है। पर्यावरण संकट इस सदी की सबसे बड़ी चुनौती के रूप में हमारे सामने है। ऐसे में सवाल यह भी है कि लोकसभा चुनाव के बाद अगली सरकार के लिए पर्यावरण और अक्षय ऊर्जा कितना बड़ा अजेंडा होगा। ऊर्जा, पर्यावरण और टिकाऊ विकास पर काम करने वाले संस्थान द एनर्जी एंड रिसोर्स इंस्टिट्यूट (TERI) के अपनी स्थापना के 50 साल पूरे करने के मौके पर अरविंद कुमार मिश्रा ने",
  "content_hash": "bc52e027a44f3586618849f733eceae9dd39e30274919628a862d9b99226b6b8",
  "token_count": 447,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "navbharat_times_pdf",
  "pdf_path": "Navbharat_Times.pdf",
  "parent_chunk_id": "61939316-af73-506c-bd31-ac5cbc64d38f",
  "chunk_index": 0,
  "page_number": 1,
  "page_range": [
    1,
    1
  ],
  "created_at": "2026-06-30T08:33:54.221182+00:00",
  "updated_at": "2026-06-30T08:33:54.221182+00:00"
}
```

## Child · `d2ba2d77-7c70-5d37-add5-1afc6f509667`

- vector: dim=3072 · [-0.0152, -0.0354, -0.0226, -0.0173, 0.0172, 0.0231, -0.0432, 0.0170, …]

```json
{
  "chunk_id": "d2ba2d77-7c70-5d37-add5-1afc6f509667",
  "document_id": "navbharat_times_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Navbharat_Times.pdf",
  "chunk_text": "�ना के 50 साल पूरे करने के मौके पर अरविंद कुमार मिश्रा ने संस्थान की डायरेक्टर जनरल डॉ\n\nविभा धवन से इन तमाम मसलों पर बातचीत की। पेश है बातचीत के अहम अंश :\n\nदेश में लोकसभा चुनाव की प्रक्रिया शुरू हो गई हैं। मतदाता जलवायु के मुद्दे पर कितने संवेदनशील हैं ?",
  "content_hash": "e4546fa5992967148451d156ffa284148e2849917a208cf18adab7bf0f060b50",
  "token_count": 239,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "navbharat_times_pdf",
  "pdf_path": "Navbharat_Times.pdf",
  "parent_chunk_id": "61939316-af73-506c-bd31-ac5cbc64d38f",
  "chunk_index": 1,
  "page_number": 1,
  "page_range": [
    1,
    1
  ],
  "created_at": "2026-06-30T08:33:54.221182+00:00",
  "updated_at": "2026-06-30T08:33:54.221182+00:00"
}
```

## Child · `38359d3b-8d8a-5c3f-bc08-383f4f235d7e`

- vector: dim=3072 · [-0.0112, -0.0375, -0.0179, 0.0107, 0.0156, -0.0097, -0.0261, -0.0160, …]

```json
{
  "chunk_id": "38359d3b-8d8a-5c3f-bc08-383f4f235d7e",
  "document_id": "navbharat_times_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Navbharat_Times.pdf",
  "chunk_text": "ं। मतदाता जलवायु के मुद्दे पर कितने संवेदनशील हैं ? जलवायु संकट से कोई भी व्यक्ति अछूता नहीं है, वह चाहे किसी भी जाति या धर्म का हो। हर भौगोलिक क्षेत्र में पर्यावरण संकट का असर दिख रहा है। लोकसभा चुनाव भारतीय लोकतंत्र का सबसे बड़ा उत्सव है, लेकिन दुर्भाग्य से राजनीतिक दलों के घोषणापत्र में पर्यावरण और जलवायु समाधान को वह अहमियत नहीं मिल पाती, जो मिलनी चाहिए। यदि वोटर पर्यावरण के प्रति संवेदनशील होंगे तो वे इन मुद्दों को आगे ले जाने वाले जनप्रतिनिधियों",
  "content_hash": "a1e6689cbc8d8df3412d2d8b84bdf94fc64e85734634e2671bd22096ff11947b",
  "token_count": 449,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "navbharat_times_pdf",
  "pdf_path": "Navbharat_Times.pdf",
  "parent_chunk_id": "61939316-af73-506c-bd31-ac5cbc64d38f",
  "chunk_index": 2,
  "page_number": 1,
  "page_range": [
    1,
    1
  ],
  "created_at": "2026-06-30T08:33:54.221182+00:00",
  "updated_at": "2026-06-30T08:33:54.221182+00:00"
}
```

## Child · `20a17d8b-a85b-51e3-8e51-74ff01ba4290`

- vector: dim=3072 · [-0.0536, -0.0236, -0.0170, 0.0163, -0.0168, -0.0120, 0.0197, 0.0204, …]

```json
{
  "chunk_id": "20a17d8b-a85b-51e3-8e51-74ff01ba4290",
  "document_id": "navbharat_times_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Navbharat_Times.pdf",
  "chunk_text": "�ो वे इन मुद्दों को आगे ले जाने वाले जनप्रतिनिधियों को ही संसद और राज्यों की विधानसभाओं में भेजेंगे।\n\n· अगली सरकार के लिए नेट जीरो का लक्ष्य विकासशील देश के लिए फॉसिल फ्यूल से बाहर आकर कितना चुनौतीपूर्ण होगा?",
  "content_hash": "d36a4c7e18b922dfb04573b63811aa8ffc612c881dd5b2a94ac5145af790a924",
  "token_count": 205,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "navbharat_times_pdf",
  "pdf_path": "Navbharat_Times.pdf",
  "parent_chunk_id": "61939316-af73-506c-bd31-ac5cbc64d38f",
  "chunk_index": 3,
  "page_number": 1,
  "page_range": [
    1,
    1
  ],
  "created_at": "2026-06-30T08:33:54.221182+00:00",
  "updated_at": "2026-06-30T08:33:54.221182+00:00"
}
```

## Child · `37f9d48f-f41b-5a4b-a647-84f3aa56005c`

- vector: dim=3072 · [-0.0442, -0.0287, -0.0124, -0.0010, -0.0190, -0.0426, 0.0098, 0.0213, …]

```json
{
  "chunk_id": "37f9d48f-f41b-5a4b-a647-84f3aa56005c",
  "document_id": "navbharat_times_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Navbharat_Times.pdf",
  "chunk_text": "फॉसिल फ्यूल से बाहर आकर कितना चुनौतीपूर्ण होगा? भारत ने 2070 में नेट जीरो इकॉनमी बनने का लक्ष्य रखा है। इसके लिए 2030 तक हमें अपनी बिजली खपत का 50% नॉन फॉसिल फ्यूल से जुटाना होगा। केंद्र सरकार ने बायोफ्यूल पॉलिसी, ग्रीन हाइड्रोजन मिशन समेत कई नीतिगत कदम उठाए हैं। EV को प्रमोट किया जा रहा है। जलवायु संकट से निपटने की कोई भी प्लानिंग टेक्नॉलजी और इनोवेशन से आगे बढ़ेगी।\n· 5 ट्रिलियन डॉलर इकॉनमी का लक्ष्य जलवायु अर्थव्यवस्था से कैसे लिंक होगा?",
  "content_hash": "a82119b0722abb10874e9ecfbdc3b4384118970611bee83d5b47393a17a2d3bd",
  "token_count": 448,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "navbharat_times_pdf",
  "pdf_path": "Navbharat_Times.pdf",
  "parent_chunk_id": "61939316-af73-506c-bd31-ac5cbc64d38f",
  "chunk_index": 4,
  "page_number": 1,
  "page_range": [
    1,
    1
  ],
  "created_at": "2026-06-30T08:33:54.221182+00:00",
  "updated_at": "2026-06-30T08:33:54.221182+00:00"
}
```

## Child · `3ca1d031-3e1e-5fcf-8b5e-f88503a754f5`

- vector: dim=3072 · [-0.0353, -0.0198, -0.0234, 0.0234, -0.0172, -0.0407, 0.0154, 0.0055, …]

```json
{
  "chunk_id": "3ca1d031-3e1e-5fcf-8b5e-f88503a754f5",
  "document_id": "navbharat_times_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Navbharat_Times.pdf",
  "chunk_text": "का लक्ष्य जलवायु अर्थव्यवस्था से कैसे लिंक होगा? प्रॉडक्शन और डिस्ट्रिब्यूशन को सस्टेनेबल बनाने के साथ डिजिटिल इकॉनमी पर जोर देना होगा। तकनीक आधारित विकास से क्लाइमेट एक्शन को मजबूती मिलती है। रिन्यूएबल एनर्जी और टिकाऊ इंफ्रास्ट्रक्चर से प्रॉडक्टिविटी बढ़ानी होगी। ऐसा इंफ्रास्ट्रक्चर खड़ा किया जाए जो जलवायु संकट से निपटने में कारगर हो।\n· रिन्यूएबल एनर्जी को कॉस्ट इफेक्टिव बनाते हुए ऊर्जा सुरक्षा कैसे हासिल होगी?",
  "content_hash": "b18f0a8d2a6663be02e3d3d9dc7f11d7c70b527beb45dd787e461f957d491dcb",
  "token_count": 420,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "navbharat_times_pdf",
  "pdf_path": "Navbharat_Times.pdf",
  "parent_chunk_id": "61939316-af73-506c-bd31-ac5cbc64d38f",
  "chunk_index": 5,
  "page_number": 1,
  "page_range": [
    1,
    1
  ],
  "created_at": "2026-06-30T08:33:54.221182+00:00",
  "updated_at": "2026-06-30T08:33:54.221182+00:00"
}
```

## Child · `a3f609e5-18fb-5d4d-b3bb-606a579a20c0`

- vector: dim=3072 · [-0.0186, -0.0096, -0.0085, 0.0262, -0.0016, -0.0118, -0.0170, -0.0260, …]

```json
{
  "chunk_id": "a3f609e5-18fb-5d4d-b3bb-606a579a20c0",
  "document_id": "navbharat_times_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Navbharat_Times.pdf",
  "chunk_text": "� इफेक्टिव बनाते हुए ऊर्जा सुरक्षा कैसे हासिल होगी? प्रति व्यक्ति ऊर्जा खपत का जो वैश्विक अनुपात है, उसमें हमारा औसत 1/3 है। एनर्जी डायवर्सिफिकेशन की\n\nविश्व बैंक के मुताबिक, भारत ग्लोबल वॉर्मिंग, बढ़ते कार्बन उत्सर्जन और प्लास्टिक प्रदूषण का सबसे बड़ा हॉटस्पॉट है। तापमान में अप्रत्याशित वृद्धि हृदय रोग, मलेरिया और डेंगू जैसी बीमारियों की वजह बन रही है। इससे स्वास्थ्य सेवाओं की लागत भी बढ़ती है। हीटवेव, तूफान, बाढ़ से विस्थापन और मानसिक अवसाद के मामले बढ़ रहे हैं",
  "content_hash": "82e1298b5edf870b7bd1fdfdfa57bc1ed2dcb3876e6c2436fdd767a5cb8abd3b",
  "token_count": 482,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "navbharat_times_pdf",
  "pdf_path": "Navbharat_Times.pdf",
  "parent_chunk_id": "61939316-af73-506c-bd31-ac5cbc64d38f",
  "chunk_index": 6,
  "page_number": 1,
  "page_range": [
    1,
    1
  ],
  "created_at": "2026-06-30T08:33:54.221182+00:00",
  "updated_at": "2026-06-30T08:33:54.221182+00:00"
}
```

## Child · `4fa3ffa1-8f64-56d9-b99c-5f8cb0312ba0`

- vector: dim=3072 · [-0.0127, 0.0077, -0.0053, -0.0024, 0.0238, -0.0189, -0.0183, -0.0250, …]

```json
{
  "chunk_id": "4fa3ffa1-8f64-56d9-b99c-5f8cb0312ba0",
  "document_id": "navbharat_times_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Navbharat_Times.pdf",
  "chunk_text": "़ से विस्थापन और मानसिक अवसाद के मामले बढ़ रहे हैं मुताबिक भारत ग्लोबल वॉर्मिंग, बढ़ते कार्बन उत्सर्जन और प्लास्टिक प्रदूषण का सबसे बड़ा हॉटस्पॉट है। तापमान में अप्रत्याशित वृद्धि हृदय रोग, मलेरिया और डेंगू जैसी बीमारियों की वजह बन रही है। इससे स्वास्थ्य सेवाओं की लागत भी बढ़ती है। हीटवेव, तूफान, बाढ़ से विस्थापन और सप्ताह का इंटरव्यू मानसिक अवसाद के बढ़ते मामले हमारे डॉ",
  "content_hash": "81cdb5075d68fa04909eb01506c7965349e905bdb2a9016e81350db0741fb1cc",
  "token_count": 392,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "navbharat_times_pdf",
  "pdf_path": "Navbharat_Times.pdf",
  "parent_chunk_id": "61939316-af73-506c-bd31-ac5cbc64d38f",
  "chunk_index": 7,
  "page_number": 1,
  "page_range": [
    1,
    1
  ],
  "created_at": "2026-06-30T08:33:54.221182+00:00",
  "updated_at": "2026-06-30T08:33:54.221182+00:00"
}
```

## Child · `1391fed5-e211-5a0e-8d80-3e6d11a4fe74`

- vector: dim=3072 · [-0.0202, -0.0196, -0.0062, 0.0083, 0.0205, -0.0258, -0.0328, -0.0159, …]

```json
{
  "chunk_id": "1391fed5-e211-5a0e-8d80-3e6d11a4fe74",
  "document_id": "navbharat_times_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Navbharat_Times.pdf",
  "chunk_text": "ा इंटरव्यू मानसिक अवसाद के बढ़ते मामले हमारे डॉ विभा धवन सामने हैं। जलवायु में हो रहा बदलाव जल संकट को भी बढ़ाएगा। आजीविकाओं के क्षेत्र रिन्यूएबल से हासिल कर ली है। पेट्रोल में 20% एथेनॉल मिश्रण का लक्ष्य अगले साल पूरा हो सकता है। किसी भी में कृषि, मछली पालन, वनोपज और टूरिज्म पर इसका सबसे ज्यादा प्रभाव पड़ने का अनुमान है। यह सप्लाई चेन को बाधित करता है। ऐसे में बेरोजगारी और एनर्जी सिक्योरिटी हासिल करना आसान नहीं है। ऐसे में छंटनी के संकट से बचने के",
  "content_hash": "94b321ba45acf33dd665cb0f56758b13fecc1ddd18704eef1e62f1ee2fcc1f57",
  "token_count": 449,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "navbharat_times_pdf",
  "pdf_path": "Navbharat_Times.pdf",
  "parent_chunk_id": "61939316-af73-506c-bd31-ac5cbc64d38f",
  "chunk_index": 8,
  "page_number": 1,
  "page_range": [
    1,
    1
  ],
  "created_at": "2026-06-30T08:33:54.221182+00:00",
  "updated_at": "2026-06-30T08:33:54.221182+00:00"
}
```

## Child · `cde6edc5-2942-5f7d-bd6e-c76d44d53ab5`

- vector: dim=3072 · [-0.0341, 0.0040, -0.0169, -0.0023, -0.0184, 0.0005, 0.0034, -0.0024, …]

```json
{
  "chunk_id": "cde6edc5-2942-5f7d-bd6e-c76d44d53ab5",
  "document_id": "navbharat_times_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Navbharat_Times.pdf",
  "chunk_text": "करना आसान नहीं है। ऐसे में छंटनी के संकट से बचने के लिए हर व्यक्ति, संस्थान और परंपरागत ऊर्जा स्रोत को भी बढ़ाना होगा। एनर्जी ट्रांजिशन समुदाय को अपनी भूमिका तय करनी होगी। के लिए भारत ने EV को बढ़ावा देने समेत कई साहसिक कदम उठाए हैं।\n\n· जलवायु संकट के मोर्चे पर डिवेलप और नॉन- डिवेलपिंग देश आमने-सामने नजर आते हैं ...\n· एनर्जी कंजर्वेशन पर कुछ हद तक अवेयरनेस आई है, लेकिन पानी को लेकर हम अ",
  "content_hash": "745131be94bd19a72e6eb1b51b73f3f36e620e6db7295a450251b38813bdb763",
  "token_count": 379,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "navbharat_times_pdf",
  "pdf_path": "Navbharat_Times.pdf",
  "parent_chunk_id": "61939316-af73-506c-bd31-ac5cbc64d38f",
  "chunk_index": 9,
  "page_number": 1,
  "page_range": [
    1,
    1
  ],
  "created_at": "2026-06-30T08:33:54.221182+00:00",
  "updated_at": "2026-06-30T08:33:54.221182+00:00"
}
```
