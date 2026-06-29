# Qdrant points — Navbharat_Times.pdf

- points (rows upserted): **13**
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
  "section_heading": "क्लाइमेट चेंज की भेंट चढ़ेंगी करोड़ों नौकरियां",
  "chunk_text": "क्लाइमेट चेंज की भेंट चढ़ेंगी करोड़ों नौकरियां\n\nमौसम में अप्रत्याशित बदलाव से लोगों को बहुत परेशानी\nहो रही है। पर्यावरण संकट इस सदी की सबसे बड़ी\nचुनौती के रूप में हमारे सामने है। ऐसे में सवाल यह भी\nहै कि लोकसभा चुनाव के बाद अगली सरकार के लिए\nपर्यावरण और अक्षय ऊर्जा कितना बड़ा अजेंडा होगा।\nऊर्जा, पर्यावरण और टिकाऊ विकास पर काम करने\nवाले संस्थान द एनर्जी एंड रिसोर्स इंस्टिट्यूट (TERI)\nके अपनी स्थापना के 50 साल पूरे करने के मौके पर\nअरविंद कुमार मिश्रा ने संस्थान की डायरेक्टर जनरल\nडॉ. विभा धवन से इन तमाम मसलों पर बातचीत की।\nपेश है बातचीत के अहम अंश :\n\n· देश में लोकसभा चुनाव की प्रक्रिया शुरू हो गई\n\n… [+1258 more chars]",
  "content_hash": "191c9f1b8d4baa6d30a5a86218693a076a79d54d6b3841cdfb894a60f6e41f84",
  "token_count": 1863,
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
  "created_at": "2026-06-29T10:56:04.435982+00:00",
  "updated_at": "2026-06-29T10:56:04.435982+00:00"
}
```

## Child · `92a1660e-82b1-5836-b397-0edc2b8f0902`

- vector: dim=3072 · [-0.0125, -0.0395, -0.0039, -0.0225, 0.0091, -0.0111, -0.0133, 0.0191, …]

```json
{
  "chunk_id": "92a1660e-82b1-5836-b397-0edc2b8f0902",
  "document_id": "navbharat_times_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Navbharat_Times.pdf",
  "section_heading": "क्लाइमेट चेंज की भेंट चढ़ेंगी करोड़ों नौकरियां",
  "chunk_text": "मौसम में अप्रत्याशित बदलाव से लोगों को बहुत परेशानी\nहो रही है। पर्यावरण संकट इस सदी की सबसे बड़ी\nचुनौती के रूप में हमारे सामने है। ऐसे में सवाल यह भी\nहै कि लोकसभा चुनाव के बाद अगली सरकार के लिए\nपर्यावरण और अक्षय ऊर्जा कितना बड़ा अजेंडा होगा।\nऊर्जा, पर्यावरण और टिकाऊ विकास पर काम करने\nवाले संस्थान द एनर्जी एंड रिसोर्स इंस्टिट्यूट (TERI)\nके अपनी स्थापना के 50 साल पूरे करने के मौके पर",
  "content_hash": "d71b4d3ab0b5061f1737b5af97eeee95579c65473b0e08f335f295be2091f12e",
  "token_count": 378,
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
  "created_at": "2026-06-29T10:56:04.435982+00:00",
  "updated_at": "2026-06-29T10:56:04.435982+00:00"
}
```

## Child · `d2ba2d77-7c70-5d37-add5-1afc6f509667`

- vector: dim=3072 · [-0.0177, -0.0244, -0.0253, -0.0317, 0.0024, 0.0171, -0.0243, 0.0178, …]

```json
{
  "chunk_id": "d2ba2d77-7c70-5d37-add5-1afc6f509667",
  "document_id": "navbharat_times_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Navbharat_Times.pdf",
  "section_heading": "क्लाइमेट चेंज की भेंट चढ़ेंगी करोड़ों नौकरियां",
  "chunk_text": "�्यूट (TERI)\nके अपनी स्थापना के 50 साल पूरे करने के मौके पर अरविंद कुमार मिश्रा ने संस्थान की डायरेक्टर जनरल\nडॉ. विभा धवन से इन तमाम मसलों पर बातचीत की।\nपेश है बातचीत के अहम अंश :\n\n· देश में लोकसभा चुनाव की प्रक्रिया शुरू हो गई हैं।\nमतदाता जलवायु के मुद्दे पर कितने संवेदनशील हैं?",
  "content_hash": "ba5322bde7d91ba3188b358bfa87c0fea1c2e933b8bdcab1bd427a2192519306",
  "token_count": 266,
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
  "created_at": "2026-06-29T10:56:04.435982+00:00",
  "updated_at": "2026-06-29T10:56:04.435982+00:00"
}
```

## Child · `38359d3b-8d8a-5c3f-bc08-383f4f235d7e`

- vector: dim=3072 · [-0.0066, -0.0266, -0.0152, 0.0120, 0.0203, -0.0100, -0.0304, -0.0201, …]

```json
{
  "chunk_id": "38359d3b-8d8a-5c3f-bc08-383f4f235d7e",
  "document_id": "navbharat_times_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Navbharat_Times.pdf",
  "section_heading": "क्लाइमेट चेंज की भेंट चढ़ेंगी करोड़ों नौकरियां",
  "chunk_text": "।\nमतदाता जलवायु के मुद्दे पर कितने संवेदनशील हैं? जलवायु संकट से कोई भी व्यक्ति अछूता नहीं है, वह\nचाहे किसी भी जाति या धर्म का हो। हर भौगोलिक क्षेत्र\nमें पर्यावरण संकट का असर दिख रहा है। लोकसभा\nचुनाव भारतीय लोकतंत्र का सबसे बड़ा उत्सव है, लेकिन\nदुर्भाग्य से राजनीतिक दलों के घोषणापत्र में पर्यावरण और\nजलवायु समाधान को वह अहमियत नहीं मिल पाती, जो\nमिलनी चाहिए। यदि वोटर पर्यावरण के प्रति संवेदनशील",
  "content_hash": "a29d0c788c7f6e175eb03df05edbdde4e5f385ac74e70c66bde2b757b3669481",
  "token_count": 398,
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
  "created_at": "2026-06-29T10:56:04.435982+00:00",
  "updated_at": "2026-06-29T10:56:04.435982+00:00"
}
```

## Child · `20a17d8b-a85b-51e3-8e51-74ff01ba4290`

- vector: dim=3072 · [-0.0432, -0.0347, -0.0145, 0.0098, -0.0042, -0.0205, -0.0108, 0.0149, …]

```json
{
  "chunk_id": "20a17d8b-a85b-51e3-8e51-74ff01ba4290",
  "document_id": "navbharat_times_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Navbharat_Times.pdf",
  "section_heading": "क्लाइमेट चेंज की भेंट चढ़ेंगी करोड़ों नौकरियां",
  "chunk_text": "मिलनी चाहिए। यदि वोटर पर्यावरण के प्रति संवेदनशील होंगे तो वे इन मुद्दों को आगे ले जाने वाले जनप्रतिनिधियों\nको ही संसद और राज्यों की विधानसभाओं में भेजेंगे।\n· अगली सरकार के लिए नेट जीरो का लक्ष्य\nकितना चुनौतीपूर्ण होगा?",
  "content_hash": "466794dcc026b1a26514ed1ed97b1dac53c064fafa8f8cd960e1662ab3ff5fa7",
  "token_count": 219,
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
  "created_at": "2026-06-29T10:56:04.435982+00:00",
  "updated_at": "2026-06-29T10:56:04.435982+00:00"
}
```

## Child · `37f9d48f-f41b-5a4b-a647-84f3aa56005c`

- vector: dim=3072 · [-0.0297, -0.0271, -0.0131, -0.0051, -0.0230, -0.0310, 0.0007, 0.0202, …]

```json
{
  "chunk_id": "37f9d48f-f41b-5a4b-a647-84f3aa56005c",
  "document_id": "navbharat_times_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Navbharat_Times.pdf",
  "section_heading": "क्लाइमेट चेंज की भेंट चढ़ेंगी करोड़ों नौकरियां",
  "chunk_text": "के लिए नेट जीरो का लक्ष्य\nकितना चुनौतीपूर्ण होगा? भारत ने 2070 में नेट जीरो इकॉनमी बनने का लक्ष्य\nरखा है। इसके लिए 2030 तक हमें अपनी बिजली खपत\nका 50% नॉन फॉसिल फ्यूल से जुटाना होगा। केंद्र सरकार\nने बायोफ्यूल पॉलिसी, ग्रीन हाइड्रोजन मिशन समेत कई\nनीतिगत कदम उठाए हैं। EV को प्रमोट किया जा रहा है।\nजलवायु संकट से निपटने की कोई भी प्लानिंग टेक्नॉलजी\nऔर इनोवेशन से आगे बढ़ेगी।",
  "content_hash": "a76b76f6cc894d608532082eb756ff58be30b4287bfbcca0e5043c6230471389",
  "token_count": 375,
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
  "created_at": "2026-06-29T10:56:04.435982+00:00",
  "updated_at": "2026-06-29T10:56:04.435982+00:00"
}
```

## Child · `3ca1d031-3e1e-5fcf-8b5e-f88503a754f5`

- vector: dim=3072 · [-0.0476, -0.0139, -0.0183, 0.0103, -0.0008, -0.0512, 0.0179, 0.0220, …]

```json
{
  "chunk_id": "3ca1d031-3e1e-5fcf-8b5e-f88503a754f5",
  "document_id": "navbharat_times_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Navbharat_Times.pdf",
  "section_heading": "क्लाइमेट चेंज की भेंट चढ़ेंगी करोड़ों नौकरियां",
  "chunk_text": "ानिंग टेक्नॉलजी\nऔर इनोवेशन से आगे बढ़ेगी। · 5 ट्रिलियन डॉलर इकॉनमी का लक्ष्य जलवायु\nअर्थव्यवस्था से कैसे लिंक होगा?\n\nप्रॉडक्शन और डिस्ट्रिब्यूशन को सस्टेनेबल बनाने के\nसाथ डिजिटिल इकॉनमी पर जोर देना होगा। तकनीक\nआधारित विकास से क्लाइमेट एक्शन को मजबूती\nमिलती है। रिन्यूएबल एनर्जी और टिकाऊ इंफ्रास्ट्रक्चर से\nप्रॉडक्टिविटी बढ़ानी होगी। ऐसा इंफ्रास्ट्रक्चर खड़ा किया\nजाए जो जलवायु संकट से निपटने में कारगर हो।",
  "content_hash": "059832068ed9344e26c9c0057a0acbba01d0486c4d117946d049e17b88d3f79f",
  "token_count": 422,
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
  "created_at": "2026-06-29T10:56:04.435982+00:00",
  "updated_at": "2026-06-29T10:56:04.435982+00:00"
}
```

## Parent · `b6a5d9e4-dc61-5a05-9968-c702affbaa63`

- vector: dim=3072 · [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, …]

```json
{
  "chunk_id": "b6a5d9e4-dc61-5a05-9968-c702affbaa63",
  "document_id": "navbharat_times_pdf",
  "is_parent": true,
  "source_type": "pdf",
  "title": "Navbharat_Times.pdf",
  "section_heading": "· रिन्यूएबल एनर्जी को कॉस्ट इफेक्टिव बनाते हुए ऊर्जा सुरक्षा कैसे हासिल होगी?",
  "chunk_text": "· रिन्यूएबल एनर्जी को कॉस्ट इफेक्टिव बनाते हुए ऊर्जा सुरक्षा कैसे हासिल होगी?\n\nप्रति व्यक्ति ऊर्जा खपत का जो वैश्विक अनुपात है,\nउसमें हमारा औसत 1/3 है। एनर्जी डायवर्सिफिकेशन की\nराह पर बढ़ते हुए भारत ने 43% बिजली उत्पादन क्षमता\n\nसप्ताह का इंटरव्यू\n\nडॉ. विभा धवन\n\nरीन्यूएबल से हासिल कर ली है। पेट्रोल में 20% एथेनॉल\nमिश्रण का लक्ष्य अगले साल पूरा हो सकता है। किसी भी\nविकासशील देश के लिए फॉसिल फ्यूल से बाहर आकर\nएनर्जी सिक्योरिटी हासिल करना आसान नहीं है। ऐसे में\nपरंपरागत ऊर्जा स्रोत को भी बढ़ाना होगा। एनर्जी ट्रांजिशन\nके लिए भारत ने EV को बढ़ावा देने समेत कई साहसिक\nकदम उठाए हैं।\n\n· जलवायु संकट के मोर\n\n… [+1017 more chars]",
  "content_hash": "f5be05446663ce321eef344f1884844c6843361d841ef98b46a8df2ab8c6ac5b",
  "token_count": 1648,
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
  "created_at": "2026-06-29T10:56:04.435982+00:00",
  "updated_at": "2026-06-29T10:56:04.435982+00:00"
}
```

## Child · `a3f609e5-18fb-5d4d-b3bb-606a579a20c0`

- vector: dim=3072 · [0.0069, -0.0177, -0.0069, 0.0201, -0.0198, -0.0079, 0.0002, 0.0334, …]

```json
{
  "chunk_id": "a3f609e5-18fb-5d4d-b3bb-606a579a20c0",
  "document_id": "navbharat_times_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Navbharat_Times.pdf",
  "section_heading": "· रिन्यूएबल एनर्जी को कॉस्ट इफेक्टिव बनाते हुए ऊर्जा सुरक्षा कैसे हासिल होगी?",
  "chunk_text": "प्रति व्यक्ति ऊर्जा खपत का जो वैश्विक अनुपात है,\nउसमें हमारा औसत 1/3 है। एनर्जी डायवर्सिफिकेशन की\nराह पर बढ़ते हुए भारत ने 43% बिजली उत्पादन क्षमता\n\nसप्ताह का इंटरव्यू\n\nडॉ. विभा धवन",
  "content_hash": "843c8196a9aeaacf86503f58c788a24b7d8a0e1a3347acd71e39e99e35b06de4",
  "token_count": 183,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "navbharat_times_pdf",
  "pdf_path": "Navbharat_Times.pdf",
  "parent_chunk_id": "b6a5d9e4-dc61-5a05-9968-c702affbaa63",
  "chunk_index": 6,
  "page_number": 1,
  "page_range": [
    1,
    1
  ],
  "created_at": "2026-06-29T10:56:04.435982+00:00",
  "updated_at": "2026-06-29T10:56:04.435982+00:00"
}
```

## Child · `4fa3ffa1-8f64-56d9-b99c-5f8cb0312ba0`

- vector: dim=3072 · [-0.0219, 0.0211, -0.0134, 0.0057, -0.0223, -0.0025, -0.0148, 0.0117, …]

```json
{
  "chunk_id": "4fa3ffa1-8f64-56d9-b99c-5f8cb0312ba0",
  "document_id": "navbharat_times_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Navbharat_Times.pdf",
  "section_heading": "· रिन्यूएबल एनर्जी को कॉस्ट इफेक्टिव बनाते हुए ऊर्जा सुरक्षा कैसे हासिल होगी?",
  "chunk_text": "�त्पादन क्षमता\n\nसप्ताह का इंटरव्यू\n\nडॉ. विभा धवन रीन्यूएबल से हासिल कर ली है। पेट्रोल में 20% एथेनॉल\nमिश्रण का लक्ष्य अगले साल पूरा हो सकता है। किसी भी\nविकासशील देश के लिए फॉसिल फ्यूल से बाहर आकर\nएनर्जी सिक्योरिटी हासिल करना आसान नहीं है। ऐसे में\nपरंपरागत ऊर्जा स्रोत को भी बढ़ाना होगा। एनर्जी ट्रांजिशन\nके लिए भारत ने EV को बढ़ावा देने समेत कई साहसिक\nकदम उठाए हैं।\n\n· जलवायु संकट के मोर्चे पर डिवेलप और नॉन-\nडिवेलपिंग देश आमने-सामने नजर आते हैं ...",
  "content_hash": "fbe08967c1cb0f0ba58787ee613a7caf8321811e6abb4be1026e458a429db636",
  "token_count": 445,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "navbharat_times_pdf",
  "pdf_path": "Navbharat_Times.pdf",
  "parent_chunk_id": "b6a5d9e4-dc61-5a05-9968-c702affbaa63",
  "chunk_index": 7,
  "page_number": 1,
  "page_range": [
    1,
    1
  ],
  "created_at": "2026-06-29T10:56:04.435982+00:00",
  "updated_at": "2026-06-29T10:56:04.435982+00:00"
}
```

## Child · `1391fed5-e211-5a0e-8d80-3e6d11a4fe74`

- vector: dim=3072 · [-0.0110, -0.0034, -0.0091, 0.0236, 0.0075, -0.0304, 0.0069, -0.0145, …]

```json
{
  "chunk_id": "1391fed5-e211-5a0e-8d80-3e6d11a4fe74",
  "document_id": "navbharat_times_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Navbharat_Times.pdf",
  "section_heading": "· रिन्यूएबल एनर्जी को कॉस्ट इफेक्टिव बनाते हुए ऊर्जा सुरक्षा कैसे हासिल होगी?",
  "chunk_text": "प और नॉन-\nडिवेलपिंग देश आमने-सामने नजर आते हैं ... विकासशील देशों ने जलवायु संकट का सबसे अधिक\nखामियाजा भुगता है। मौसम में अप्रत्याशित बदलाव का\nसबसे ज्यादा असर छोटे, द्वीपीय और विकासशील देशों\nको हुआ है। क्लाइमेट जस्टिस की दिशा में अनुकूलन\n(अडॉप्टेशन) की पहल को जमीन पर सफल बनाने के\nलिए पैसे और टेक्नॉलजी की दरकार है। आखिर कोई भी\nदेश विकास की अपनी जरूरत को टाल नहीं सकता।\nविकसित देशों ने संसाधनों का सबसे अधिक उपभोग",
  "content_hash": "5c49e91a98f90444c536e2bc4f5c6bad7d49c3e4b31a5fb55fadbb67d75b7d54",
  "token_count": 422,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "navbharat_times_pdf",
  "pdf_path": "Navbharat_Times.pdf",
  "parent_chunk_id": "b6a5d9e4-dc61-5a05-9968-c702affbaa63",
  "chunk_index": 8,
  "page_number": 1,
  "page_range": [
    1,
    1
  ],
  "created_at": "2026-06-29T10:56:04.435982+00:00",
  "updated_at": "2026-06-29T10:56:04.435982+00:00"
}
```

## Child · `cde6edc5-2942-5f7d-bd6e-c76d44d53ab5`

- vector: dim=3072 · [-0.0384, -0.0469, -0.0074, 0.0164, 0.0014, 0.0116, 0.0356, -0.0080, …]

```json
{
  "chunk_id": "cde6edc5-2942-5f7d-bd6e-c76d44d53ab5",
  "document_id": "navbharat_times_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Navbharat_Times.pdf",
  "section_heading": "· रिन्यूएबल एनर्जी को कॉस्ट इफेक्टिव बनाते हुए ऊर्जा सुरक्षा कैसे हासिल होगी?",
  "chunk_text": "ता।\nविकसित देशों ने संसाधनों का सबसे अधिक उपभोग किया है, इसलिए उन्हें धरती पर छाए संकट से लड़ाई की\nअगुआई भी करनी चाहिए।\n\nग्लोबल वॉर्मिंग हेल्थ और जॉब क्रिएशन के\nमोर्चे पर कितना बड़ा संकट पैदा कर सकता है?\n\n2030 तक दुनिया भर में 8 करोड़ नौकरियां जलवायु\nसंकट की चपेट में होंगी। इनमें 3 करोड़ आजीविकाएं\nअकेले भारत में प्रभावित हो सकती हैं। विश्व बैंक के",
  "content_hash": "8b00a4ffd134c5d3eb952582b29e21bd41e66d20ff14420b33f572d0a31ae33e",
  "token_count": 355,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "navbharat_times_pdf",
  "pdf_path": "Navbharat_Times.pdf",
  "parent_chunk_id": "b6a5d9e4-dc61-5a05-9968-c702affbaa63",
  "chunk_index": 9,
  "page_number": 1,
  "page_range": [
    1,
    1
  ],
  "created_at": "2026-06-29T10:56:04.435982+00:00",
  "updated_at": "2026-06-29T10:56:04.435982+00:00"
}
```

## Child · `9bbe0f8c-ad9b-599f-9790-06320e3757cb`

- vector: dim=3072 · [-0.0261, -0.0026, 0.0049, 0.0148, 0.0404, -0.0208, -0.0154, -0.0284, …]

```json
{
  "chunk_id": "9bbe0f8c-ad9b-599f-9790-06320e3757cb",
  "document_id": "navbharat_times_pdf",
  "is_parent": false,
  "source_type": "pdf",
  "title": "Navbharat_Times.pdf",
  "section_heading": "· रिन्यूएबल एनर्जी को कॉस्ट इफेक्टिव बनाते हुए ऊर्जा सुरक्षा कैसे हासिल होगी?",
  "chunk_text": "ं\nअकेले भारत में प्रभावित हो सकती हैं। विश्व बैंक के विश्व बैंक के मुताबिक, भारत\nग्लोबल वॉर्मिंग, बढ़ते कार्बन\nउत्सर्जन और प्लास्टिक प्रदूषण\nका सबसे बड़ा हॉटस्पॉट है। तापमान में\nअप्रत्याशित वृद्धि हृदय रोग, मलेरिया और\nडेंगू जैसी बीमारियों की वजह बन रही है।\nइससे स्वास्थ्य सेवाओं की लागत भी बढ़ती\nहै। हीटवेव, तूफान, बाढ़ से विस्थापन और\nमानसि",
  "content_hash": "2cc1277256e26fa55f8c6bb79052208a7372e6556bbfada53ac1b9e3ebe78a29",
  "token_count": 363,
  "doc_version": 1,
  "is_current": true,
  "tenant_id": "default",
  "acl": [
    "public"
  ],
  "language": "en",
  "pdf_id": "navbharat_times_pdf",
  "pdf_path": "Navbharat_Times.pdf",
  "parent_chunk_id": "b6a5d9e4-dc61-5a05-9968-c702affbaa63",
  "chunk_index": 10,
  "page_number": 1,
  "page_range": [
    1,
    1
  ],
  "created_at": "2026-06-29T10:56:04.435982+00:00",
  "updated_at": "2026-06-29T10:56:04.435982+00:00"
}
```
