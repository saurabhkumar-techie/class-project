"""Cautious crop-health guidance based on farmer-selected symptoms."""

CROPS = {
    "wheat": "Wheat / गेहूं",
    "rice": "Rice / धान",
    "tomato": "Tomato / टमाटर",
    "potato": "Potato / आलू",
    "mustard": "Mustard / सरसों",
    "maize": "Maize / मक्का",
    "cotton": "Cotton / कपास",
    "sugarcane": "Sugarcane / गन्ना",
    "onion": "Onion / प्याज",
    "general": "Other crop / अन्य फसल",
}

SYMPTOMS = {
    "leaf_spots": "Brown or black spots on leaves / पत्तियों पर भूरे या काले धब्बे",
    "yellowing": "Yellowing leaves / पत्तियों का पीला पड़ना",
    "powdery_growth": "White or grey powder on leaves / पत्तियों पर सफेद या धूसर परत",
    "wilting": "Wilting or drooping / पौधे का मुरझाना",
    "holes": "Holes or chewed edges / पत्तियों में छेद या कटी किनारियां",
    "curling": "Curled or distorted leaves / पत्तियों का मुड़ना या विकृत होना",
}

_SPOT_DISEASES = {
    "wheat": "Rust or leaf blight",
    "rice": "Brown spot or rice blast",
    "tomato": "Early or late blight",
    "potato": "Early or late blight",
    "mustard": "Alternaria leaf blight",
    "maize": "Leaf blight",
    "cotton": "Bacterial blight or leaf spot",
    "onion": "Purple blotch or leaf spot",
}

_GUIDANCE = {
    "leaf_spots": {
        "cause": "Leaf-spotting diseases are possible, but nutrient issues and physical damage can look similar.",
        "cause_hi": "पत्ती के धब्बे वाले रोग संभव हैं, लेकिन पोषक तत्वों की कमी और चोट के लक्षण भी ऐसे दिख सकते हैं।",
        "steps": [
            "Photograph both sides of several affected leaves and check whether symptoms are spreading.",
            "Remove heavily affected plant debris where practical; avoid working in the crop while leaves are wet.",
        ],
        "pesticide": "Do not spray based on spots alone. If a plant-health expert confirms a fungal disease, use only a locally registered product labelled for this crop and disease, exactly as its label directs.",
        "pesticide_hi": "केवल धब्बे देखकर दवा न छिड़कें। यदि कृषि विशेषज्ञ फफूंद रोग की पुष्टि करें, तभी इस फसल और रोग के लिए पंजीकृत उत्पाद का लेबल के अनुसार उपयोग करें।",
    },
    "yellowing": {
        "cause": "Yellowing can result from waterlogging, drought, nutrient deficiency, root damage, or disease.",
        "cause_hi": "पीलापन जलभराव, सूखा, पोषक तत्वों की कमी, जड़ों की क्षति या रोग से हो सकता है।",
        "steps": [
            "Check soil moisture and drainage and compare affected plants with healthy plants nearby.",
            "Avoid applying pesticide for yellowing alone; seek a soil or crop assessment before adding fertilizer.",
        ],
        "pesticide": "No pesticide is recommended for this symptom alone. First check water, roots, and soil nutrients.",
        "pesticide_hi": "केवल इस लक्षण के आधार पर किसी कीटनाशक की सलाह नहीं दी जा सकती। पहले पानी, जड़ों और मिट्टी के पोषक तत्व जाँचें।",
    },
    "powdery_growth": {
        "cause": "A powdery fungal growth is possible; dust, spray residue, and other leaf disorders can look similar.",
        "cause_hi": "फफूंद की पाउडर जैसी परत संभव है; धूल, स्प्रे के अवशेष और अन्य समस्याएं भी ऐसी दिख सकती हैं।",
        "steps": [
            "Check whether the growth is on the leaf surface and whether nearby plants show the same pattern.",
            "Improve airflow where practical and avoid unnecessary wetting of foliage.",
        ],
        "pesticide": "If an expert confirms a fungal disease, ask for a product registered for this crop and disease. Follow the label, protective-equipment, and harvest-waiting instructions.",
        "pesticide_hi": "यदि विशेषज्ञ फफूंद रोग की पुष्टि करें, तो इस फसल और रोग के लिए पंजीकृत उत्पाद ही पूछें। लेबल, सुरक्षा उपकरण और कटाई-पूर्व प्रतीक्षा अवधि के निर्देश मानें।",
    },
    "wilting": {
        "cause": "Wilting may be caused by heat, lack of water, waterlogged roots, root damage, or a vascular disease.",
        "cause_hi": "मुरझाना गर्मी, पानी की कमी, जलभराव, जड़ों की क्षति या संवहनी रोग से हो सकता है।",
        "steps": [
            "Check soil moisture and drainage, then inspect the base and roots of one affected plant.",
            "Compare wilted plants across the field; seek prompt local advice if wilting is spreading.",
        ],
        "pesticide": "Do not spray without identifying the cause. Foliar pesticides usually will not correct water stress or root problems.",
        "pesticide_hi": "कारण पहचाने बिना छिड़काव न करें। पत्तियों पर दवा डालने से पानी की कमी या जड़ों की समस्या ठीक नहीं होती।",
    },
    "holes": {
        "cause": "Chewing insects or caterpillars are possible; inspect the plant for insects, eggs, and fresh damage.",
        "cause_hi": "पत्तियां खाने वाले कीट या सूंडियां संभव हैं; पौधे पर कीट, अंडे और ताजा नुकसान देखें।",
        "steps": [
            "Inspect both sides of leaves and growing tips early in the morning; note the insect and amount of fresh damage.",
            "Remove a small number of visible pests by hand where practical and protect beneficial insects.",
        ],
        "pesticide": "Use an insecticide only after the pest is identified and an expert confirms treatment is needed. Choose a product registered for that crop and pest; follow its label and pollinator precautions.",
        "pesticide_hi": "कीट की पहचान और विशेषज्ञ की सलाह के बाद ही कीटनाशक लें। फसल और कीट के लिए पंजीकृत उत्पाद चुनें और लेबल व परागणकर्ता-सुरक्षा निर्देश मानें।",
    },
    "curling": {
        "cause": "Leaf curl can be linked to sap-feeding insects, virus, heat, or herbicide drift; appearance alone cannot distinguish them.",
        "cause_hi": "पत्ती मुड़ना रस चूसने वाले कीट, विषाणु, गर्मी या शाकनाशी के बहाव से हो सकता है; केवल रूप देखकर अंतर करना संभव नहीं है।",
        "steps": [
            "Inspect leaf undersides for insects and check whether symptoms are concentrated along field edges.",
            "Avoid moving plants or tools from affected areas to healthy areas until the cause is clearer.",
        ],
        "pesticide": "Do not use an insecticide unless the pest is present and identified; insecticides do not cure viral disease or heat injury.",
        "pesticide_hi": "कीट मौजूद और पहचाना गया हो तभी कीटनाशक पर विचार करें; कीटनाशक विषाणु रोग या गर्मी से हुई क्षति का इलाज नहीं करते।",
    },
}


def get_advisory(crop_type, symptom):
    """Return a cautious advisory for supported crop and symptom identifiers."""
    if crop_type not in CROPS or symptom not in SYMPTOMS:
        return None

    guidance = _GUIDANCE[symptom]
    crop_disease = _SPOT_DISEASES.get(crop_type) if symptom == "leaf_spots" else None
    possible_cause = (
        f"Possible conditions to check include {crop_disease}; this is not a diagnosis."
        if crop_disease
        else "Several crop-health problems can cause this symptom; the cause is not confirmed."
    )

    return {
        "crop": CROPS[crop_type],
        "symptom": SYMPTOMS[symptom],
        "possible_cause": possible_cause,
        "possible_cause_hi": guidance["cause_hi"],
        "cause": guidance["cause"],
        "steps": guidance["steps"],
        "pesticide": guidance["pesticide"],
        "pesticide_hi": guidance["pesticide_hi"],
    }
