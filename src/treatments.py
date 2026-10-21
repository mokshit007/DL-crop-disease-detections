"""
Plant Disease Knowledge Base: Symptoms, Pathogen Identification, Organic & Chemical Remedies, and Prevention.
"""

TREATMENT_DATABASE = {
    # Apple
    "Apple___Apple_scab": {
        "crop": "Apple",
        "disease": "Apple Scab",
        "pathogen": "Fungus (Venturia inaequalis)",
        "symptoms": "Olive-green to dark brown velvety spots on leaves, becoming corky and causing premature leaf drop.",
        "organic": "Apply sulfur or copper soap sprays during early budding. Spray bio-fungicide containing Bacillus subtilis.",
        "chemical": "Fungicides containing Myclobutanil, Captan, or Mancozeb applied at green tip stage.",
        "prevention": "Rake and destroy fallen leaves in autumn. Prune tree canopies to improve airflow and rapid drying."
    },
    "Apple___Black_rot": {
        "crop": "Apple",
        "disease": "Black Rot (Frog-Eye Leaf Spot)",
        "pathogen": "Fungus (Botryosphaeria obtusa)",
        "symptoms": "Purple-bordered spots with tan centers ('frog-eye') on leaves; dark sunken cankers on branches; rotting fruit.",
        "organic": "Prune out diseased cankers 6-8 inches below visible damage. Apply copper-based organic fungicides.",
        "chemical": "Apply Captan or Thiophanate-methyl from silver tip through petal fall.",
        "prevention": "Remove mummified fruit hanging on branches. Disinfect pruning tools between cuts with 70% alcohol."
    },
    "Apple___Cedar_apple_rust": {
        "crop": "Apple",
        "disease": "Cedar Apple Rust",
        "pathogen": "Fungus (Gymnosporangium juniperi-virginianae)",
        "symptoms": "Bright yellow-orange circular spots on upper leaf surfaces that develop tube-like projections underneath.",
        "organic": "Apply sulfur or neem oil at blossom bud break. Remove nearby eastern red cedar trees if practical.",
        "chemical": "Fungicides containing Myclobutanil or Propiconazole applied before rain events in early spring.",
        "prevention": "Plant rust-resistant apple cultivars (e.g., Enterprise, Freedom, Liberty). Eliminate cedar galls within 500 feet."
    },
    "Apple___healthy": {
        "crop": "Apple",
        "disease": "Healthy Foliage",
        "pathogen": "None (Healthy)",
        "symptoms": "Vibrant green leaves with uniform texture and no visible spots, lesions, or curling.",
        "organic": "Maintain regular mulching, compost tea application, and balanced organic nitrogen-potassium feeding.",
        "chemical": "No chemical treatment required.",
        "prevention": "Continue seasonal dormant oil spray to control overwintering mites and aphids."
    },

    # Blueberry
    "Blueberry___healthy": {
        "crop": "Blueberry",
        "disease": "Healthy Foliage",
        "pathogen": "None (Healthy)",
        "symptoms": "Glossy green leaves free of chlorosis or necrosis; robust new shoot growth.",
        "organic": "Ensure soil pH stays between 4.5 and 5.2 using pine bark mulch and elemental sulfur.",
        "chemical": "No chemical treatment required.",
        "prevention": "Ensure deep, acidic, well-draining soil and consistent trickle irrigation."
    },

    # Cherry
    "Cherry_(including_sour)___Powdery_mildew": {
        "crop": "Cherry",
        "disease": "Powdery Mildew",
        "pathogen": "Fungus (Podosphaera clandestina)",
        "symptoms": "White to light gray powdery fungal patches on leaves and terminal shoots; leaves often cup or distort.",
        "organic": "Spray potassium bicarbonate, diluted milk solution (1:9), or Horticultural Neem oil.",
        "chemical": "Apply Myclobutanil, Quinoxyfen, or Trifloxystrobin at early petal fall.",
        "prevention": "Prune dense canopies to maximize sun penetration and air movement; avoid excess nitrogen fertilizer."
    },
    "Cherry_(including_sour)___healthy": {
        "crop": "Cherry",
        "disease": "Healthy Foliage",
        "pathogen": "None (Healthy)",
        "symptoms": "Leaves are rich dark green with clean margins, exhibiting vigorous seasonal branch growth.",
        "organic": "Apply organic compost annually and maintain a 3-inch layer of woodchip mulch around root zones.",
        "chemical": "No chemical treatment required.",
        "prevention": "Inspect leaves periodically for early signs of shot-hole fungus or aphid colonies."
    },

    # Corn (Maize)
    "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot": {
        "crop": "Corn (Maize)",
        "disease": "Cercospora Gray Leaf Spot",
        "pathogen": "Fungus (Cercospora zeae-maydis)",
        "symptoms": "Narrow rectangular, tan-to-gray lesions running parallel between leaf veins, causing blighting.",
        "organic": "Apply bio-control sprays with Trichoderma harzianum or Bacillus amyloliquefaciens.",
        "chemical": "Strobilurin or triazole fungicides (e.g., Azoxystrobin, Pyraclostrobin) at tassel emergence.",
        "prevention": "Rotate crops with non-grasses (soybeans, legumes) for at least 2 seasons. Till infested residue into soil."
    },
    "Corn_(maize)___Common_rust_": {
        "crop": "Corn (Maize)",
        "disease": "Common Rust",
        "pathogen": "Fungus (Puccinia sorghi)",
        "symptoms": "Golden-brown to cinnamon-brown powdery pustules scattered across both upper and lower leaf surfaces.",
        "organic": "Apply neem extract or sulfur dust in early morning when dew is light.",
        "chemical": "Fungicides containing Propiconazole or Azoxystrobin if pustules appear before silking stage.",
        "prevention": "Plant resistant hybrid corn varieties. Avoid planting late-season sweet corn susceptible to spore drift."
    },
    "Corn_(maize)___Northern_Leaf_Blight": {
        "crop": "Corn (Maize)",
        "disease": "Northern Corn Leaf Blight",
        "pathogen": "Fungus (Exserohilum turcicum)",
        "symptoms": "Large, elongated, cigar-shaped grayish-green to tan lesions (1 to 6 inches long).",
        "organic": "Apply copper hydroxide or compost tea sprays. Remove infected stubble post-harvest.",
        "chemical": "Foliar fungicides such as Pyraclostrobin + Fluxapyroxad (Priaxor) applied at V4 to VT stage.",
        "prevention": "Plant corn hybrids with multi-gene (Ht) resistance. Practice two-year crop rotation."
    },
    "Corn_(maize)___healthy": {
        "crop": "Corn (Maize)",
        "disease": "Healthy Foliage",
        "pathogen": "None (Healthy)",
        "symptoms": "Long, intact, deep-green arching leaves without striping, pustules, or chlorosis.",
        "organic": "Maintain adequate side-dressing of organic nitrogen and ensure deep root aeration.",
        "chemical": "No chemical treatment required.",
        "prevention": "Monitor for armyworms and corn borer moth flights using pheromone traps."
    },

    # Grape
    "Grape___Black_rot": {
        "crop": "Grape",
        "disease": "Black Rot",
        "pathogen": "Fungus (Guignardia bidwellii)",
        "symptoms": "Small circular reddish-brown leaf spots with tiny black fruiting specks; berries shrivel into hard black mummies.",
        "organic": "Apply liquid copper or Bordeaux mixture immediately before and after bloom.",
        "chemical": "Myclobutanil, Mancozeb, or Captan applied from 2-inch shoot stage through post-bloom.",
        "prevention": "Prune out mummified berry clusters during winter dormancy. Maximize canopy exposure to full sun."
    },
    "Grape___Esca_(Black_Measles)": {
        "crop": "Grape",
        "disease": "Esca (Black Measles / Trunk Disease)",
        "pathogen": "Fungal complex (Phaeomoniella chlamydospora, Fomitiporia mediterranea)",
        "symptoms": "'Tiger-stripe' chlorotic and necrotic patterns between leaf veins; dark spot speckling on berries.",
        "organic": "Paint fresh pruning wounds immediately with sealants containing Trichoderma or essential plant oils.",
        "chemical": "No curative chemical cure exists; treat pruning wounds with Thiophanate-methyl paint.",
        "prevention": "Avoid pruning during damp, foggy, or rainy weather. Remove and burn severely collapsed vines."
    },
    "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)": {
        "crop": "Grape",
        "disease": "Leaf Blight (Isariopsis Spot)",
        "pathogen": "Fungus (Pseudocercospora cladosporioides)",
        "symptoms": "Large irregular dark brown angular spots with dark halos, coalescing to cause leaf scorch and early drop.",
        "organic": "Apply copper oxychloride or botanical fungicide sprays at first signs of lesion emergence.",
        "chemical": "Foliar treatment with Carbendazim, Mancozeb, or Difenoconazole.",
        "prevention": "Keep vine rows weed-free to improve floor airflow. Prune excess suckers to facilitate sun drying."
    },
    "Grape___healthy": {
        "crop": "Grape",
        "disease": "Healthy Foliage",
        "pathogen": "None (Healthy)",
        "symptoms": "Lush, broad palmate leaves with vivid green pigmentation and no interveinal necrosis.",
        "organic": "Support with balanced potassium-magnesium fertigation and regular vine training on trellises.",
        "chemical": "No chemical treatment required.",
        "prevention": "Maintain vineyard canopy management (shoot positioning and leaf pulling around fruit zones)."
    },

    # Orange
    "Orange___Haunglongbing_(Citrus_greening)": {
        "crop": "Orange",
        "disease": "Huanglongbing (Citrus Greening)",
        "pathogen": "Bacterium (Candidatus Liberibacter asiaticus) vectored by Asian Citrus Psyllid",
        "symptoms": "Asymmetrical blotchy yellow mottling of leaves, yellow shoots, stunted trees, and small lopsided bitter fruit.",
        "organic": "Spray citrus nutritional sprays (foliar zinc, iron, manganese) to sustain tree vitality. Release Tamarixia radiata parasitoid wasps.",
        "chemical": "Systemic insecticides (Imidacloprid, Thiamethoxam) to strictly eradicate psyllid vector populations.",
        "prevention": "Source only certified disease-free nursery rootstock. Quarantine infected trees immediately."
    },

    # Peach
    "Peach___Bacterial_spot": {
        "crop": "Peach",
        "disease": "Bacterial Spot",
        "pathogen": "Bacterium (Xanthomonas arboricola pv. pruni)",
        "symptoms": "Small, angular purple-brown spots on leaves that drop out, leaving a 'shot-hole' appearance.",
        "organic": "Apply preventive copper bactericide sprays at dormant bud-swell and early petal fall.",
        "chemical": "Oxytetracycline (Mycoshield) sprays applied at shuck split and cover sprays during humid periods.",
        "prevention": "Plant resistant peach cultivars (e.g., Candor, Dixired). Avoid high-pressure overhead irrigation."
    },
    "Peach___healthy": {
        "crop": "Peach",
        "disease": "Healthy Foliage",
        "pathogen": "None (Healthy)",
        "symptoms": "Slender, glossy lanceolate leaves with smooth margins and vibrant light-to-dark green hue.",
        "organic": "Ensure deep mulch ring keeping soil moisture consistent without touching the trunk bark.",
        "chemical": "No chemical treatment required.",
        "prevention": "Apply dormant copper spray in late winter to suppress peach leaf curl spores."
    },

    # Pepper (Bell)
    "Pepper,_bell___Bacterial_spot": {
        "crop": "Bell Pepper",
        "disease": "Bacterial Spot",
        "pathogen": "Bacterium (Xanthomonas campestris pv. vesicatoria)",
        "symptoms": "Water-soaked, dark brown circular lesions on leaves, often with a yellow halo, causing severe defoliation.",
        "organic": "Apply copper sulfate or copper hydroxide combined with regular bio-fungicide (Bacillus subtilis).",
        "chemical": "Streptomycin plant spray where registered, or copper-mancozeb combination sprays.",
        "prevention": "Soak seeds in hot water (50°C for 25 min) before planting. Avoid working with wet plants."
    },
    "Pepper,_bell___healthy": {
        "crop": "Bell Pepper",
        "disease": "Healthy Foliage",
        "pathogen": "None (Healthy)",
        "symptoms": "Smooth, firm, dark green ovate leaves without curling, mottling, or necrotic puncture marks.",
        "organic": "Feed with balanced organic calcium-magnesium-phosphorus fertilizers.",
        "chemical": "No chemical treatment required.",
        "prevention": "Scout for aphids and thrips to prevent pepper mosaic virus transmission."
    },

    # Potato
    "Potato___Early_blight": {
        "crop": "Potato",
        "disease": "Early Blight",
        "pathogen": "Fungus (Alternaria solani)",
        "symptoms": "Dark brown circular spots with concentric target-like rings on older lower leaves.",
        "organic": "Apply copper octanoate or copper soap sprays every 7-10 days. Spray with Bacillus amyloliquefaciens.",
        "chemical": "Fungicides containing Chlorothalonil, Mancozeb, or Azoxystrobin.",
        "prevention": "Maintain plant vigor with adequate potassium. Water at base to avoid wetting leaves; practice 3-year rotation."
    },
    "Potato___Late_blight": {
        "crop": "Potato",
        "disease": "Late Blight",
        "pathogen": "Oomycete (Phytophthora infestans)",
        "symptoms": "Dark water-soaked lesions that rapidly expand and turn black, with white fungal fluff under leaves in high humidity.",
        "organic": "Apply fixed copper bactericides/fungicides immediately upon first weather alert.",
        "chemical": "Curative and translaminar fungicides: Mandipropamid, Cymoxanil, Fluopicolide, or Propamocarb.",
        "prevention": "Destroy all volunteer potatoes and cull piles. Use certified blight-free seed tubers."
    },
    "Potato___healthy": {
        "crop": "Potato",
        "disease": "Healthy Foliage",
        "pathogen": "None (Healthy)",
        "symptoms": "Dense, dark green pinnate foliage with sturdy stems and no wilting or spotting.",
        "organic": "Hill up soil around stems as foliage grows; apply sea kelp extract for micronutrient fortification.",
        "chemical": "No chemical treatment required.",
        "prevention": "Monitor local weather forecasts for prolonged cool, wet conditions favorable to fungal blights."
    },

    # Raspberry
    "Raspberry___healthy": {
        "crop": "Raspberry",
        "disease": "Healthy Foliage",
        "pathogen": "None (Healthy)",
        "symptoms": "Compound serrated leaves with rich green tops and pale undersides, free from yellow veins or spots.",
        "organic": "Top-dress with aged compost each spring and maintain 2-3 inches of sawdust or straw mulch.",
        "chemical": "No chemical treatment required.",
        "prevention": "Prune out spent floricanes right after harvest to maximize sunlight on primocanes."
    },

    # Soybean
    "Soybean___healthy": {
        "crop": "Soybean",
        "disease": "Healthy Foliage",
        "pathogen": "None (Healthy)",
        "symptoms": "Trifoliate leaves exhibiting uniform lime-to-forest green coloration without chlorotic flecks.",
        "organic": "Inoculate seeds with Bradyrhizobium japonicum before planting for natural nitrogen fixation.",
        "chemical": "No chemical treatment required.",
        "prevention": "Rotate with corn or sorghum to disrupt soybean cyst nematode life cycles."
    },

    # Squash
    "Squash___Powdery_mildew": {
        "crop": "Squash",
        "disease": "Powdery Mildew",
        "pathogen": "Fungus (Podosphaera xanthii)",
        "symptoms": "Talcum powder-like white fungal colonies covering both leaf surfaces, turning leaves yellow and brittle.",
        "organic": "Spray potassium bicarbonate (3 tbsp per gallon with soap) or sulfur-based organic dusts.",
        "chemical": "Systemic fungicides containing Myclobutanil or Triflumizole at initial symptom appearance.",
        "prevention": "Plant squash in full sunlight with wide spacing (at least 3-4 feet apart). Water via ground soaker hoses."
    },

    # Strawberry
    "Strawberry___Leaf_scorch": {
        "crop": "Strawberry",
        "disease": "Leaf Scorch",
        "pathogen": "Fungus (Diplocarpon earlianum)",
        "symptoms": "Numerous small, irregular purple to dark brown spots that expand and coalesce, making leaves look burnt.",
        "organic": "Spray copper-based fungicide before blossom and after harvest. Remove heavily infected leaves.",
        "chemical": "Captan or Pyraclostrobin sprays applied in spring prior to fruit set.",
        "prevention": "Renovate strawberry beds after harvest by mowing old foliage; avoid overhead sprinklers."
    },
    "Strawberry___healthy": {
        "crop": "Strawberry",
        "disease": "Healthy Foliage",
        "pathogen": "None (Healthy)",
        "symptoms": "Trifoliate, serrated, deep green glossy leaves with vigorous crown emergence and runners.",
        "organic": "Mulch with clean pine straw or black plastic; feed with slow-release organic berry fertilizer.",
        "chemical": "No chemical treatment required.",
        "prevention": "Ensure beds have excellent drainage to avoid crown and root rot."
    },

    # Tomato
    "Tomato___Bacterial_spot": {
        "crop": "Tomato",
        "disease": "Bacterial Spot",
        "pathogen": "Bacterium (Xanthomonas perforans / euvesicatoria)",
        "symptoms": "Small, dark, greasy water-soaked spots on leaves that turn brown with yellow margins; premature leaf shedding.",
        "organic": "Spray copper hydroxide or copper soap mixed with Bacillus subtilis weekly.",
        "chemical": "Combination of fixed copper fungicide plus Mancozeb to overcome copper-resistant bacterial strains.",
        "prevention": "Disinfect stakes and trellises with bleach. Avoid touching or pruning plants when foliage is wet."
    },
    "Tomato___Early_blight": {
        "crop": "Tomato",
        "disease": "Early Blight",
        "pathogen": "Fungus (Alternaria linariae / solani)",
        "symptoms": "Dark brown to black spots with distinct concentric bullseye rings, starting on the lowest leaves.",
        "organic": "Apply copper fungicide or potassium bicarbonate. Prune off bottom 12-18 inches of leaves above soil.",
        "chemical": "Chlorothalonil, Mancozeb, or Difenoconazole applied on a 7-14 day schedule.",
        "prevention": "Mulch under plants with straw to prevent soil-borne spores from splashing onto lower leaves."
    },
    "Tomato___Late_blight": {
        "crop": "Tomato",
        "disease": "Late Blight",
        "pathogen": "Oomycete (Phytophthora infestans)",
        "symptoms": "Large, irregular water-soaked pale green to dark brown lesions that expand rapidly; white fuzzy growth underneath.",
        "organic": "Immediate aggressive application of copper octanoate or copper hydroxide.",
        "chemical": "Mandipropamid (Revus), Cyazofamid (Ranman), or Fluopicolide (Presidio).",
        "prevention": "Remove and bag infected plants immediately on discovery. Choose resistant varieties like Mountain Magic."
    },
    "Tomato___Leaf_Mold": {
        "crop": "Tomato",
        "disease": "Leaf Mold",
        "pathogen": "Fungus (Passalora fulva)",
        "symptoms": "Pale yellow patches on upper leaf surfaces matching olive-green to brown velvety molds on lower surfaces.",
        "organic": "Apply copper soap or biofungicides (Serenade Garden). Vent greenhouse or tunnels aggressively.",
        "chemical": "Chlorothalonil, Myclobutanil, or Azoxystrobin.",
        "prevention": "Common in humid greenhouse conditions; keep relative humidity below 85% with fans and venting."
    },
    "Tomato___Septoria_leaf_spot": {
        "crop": "Tomato",
        "disease": "Septoria Leaf Spot",
        "pathogen": "Fungus (Septoria lycopersici)",
        "symptoms": "Numerous small circular spots with gray or tan centers and dark brown margins; tiny black specks in center.",
        "organic": "Copper-based fungicide sprays applied at first leaf spotting. Strip infected lower leaves.",
        "chemical": "Chlorothalonil or Mancozeb applied every 7-10 days in wet, warm weather.",
        "prevention": "Clean up plant debris thoroughly in autumn. Maintain minimum 2-year crop rotation."
    },
    "Tomato___Spider_mites Two-spotted_spider_mite": {
        "crop": "Tomato",
        "disease": "Two-Spotted Spider Mite Infestation",
        "pathogen": "Pest / Arachnid (Tetranychus urticae)",
        "symptoms": "Yellow or white stippling dots across leaves; fine webbing visible between stems and undersides of leaves.",
        "organic": "Spray insecticidal soap, Horticultural Rosemary/Neem oil, or release predatory mites (Phytoseiulus persimilis).",
        "chemical": "Miticide sprays containing Abamectin, Bifenazate, or Spiromesifen.",
        "prevention": "Keep plants adequately watered; hot, dry, dusty conditions trigger massive mite explosions."
    },
    "Tomato___Target_Spot": {
        "crop": "Tomato",
        "disease": "Target Spot",
        "pathogen": "Fungus (Corynespora cassiicola)",
        "symptoms": "Small brown circular lesions that expand into target-like circles with dark centers and yellow halos.",
        "organic": "Foliar copper sprays and bio-fungicides applied at early fruit set.",
        "chemical": "Boscalid, Pyraclostrobin, or Chlorothalonil.",
        "prevention": "Stake and prune plants to improve aeration. Avoid overhead sprinkle irrigation."
    },
    "Tomato___Tomato_Yellow_Leaf_Curl_Virus": {
        "crop": "Tomato",
        "disease": "Tomato Yellow Leaf Curl Virus (TYLCV)",
        "pathogen": "Geminivirus transmitted exclusively by Silverleaf Whitefly (Bemisia tabaci)",
        "symptoms": "Upward curling and cupping of leaves, prominent yellowing (chlorosis) along margins, severe plant stunting.",
        "organic": "Cover seedlings with fine insect mesh (50-mesh). Apply insecticidal soap or neem to eradicate whiteflies.",
        "chemical": "Systemic whitefly controls: Dinotefuran, Spirotetramat, or Acetamiprid.",
        "prevention": "Use yellow sticky cards to trap whiteflies. Pull and bag infected plants immediately to prevent spread."
    },
    "Tomato___Tomato_mosaic_virus": {
        "crop": "Tomato",
        "disease": "Tomato Mosaic Virus (ToMV)",
        "pathogen": "Tobamovirus (Mechanically transmitted)",
        "symptoms": "Mottled light and dark green mosaic patterns on leaves, distortion ('shoestring' appearance), reduced growth.",
        "organic": "No cure exists. Milk sprays (skim milk) can help neutralize viral particles on gardening tools.",
        "chemical": "No chemical cure exists for viral plant infections.",
        "prevention": "Disinfect tools with 20% nonfat dry milk or bleach. Smokers should wash hands before handling plants (tobacco vector)."
    },
    "Tomato___healthy": {
        "crop": "Tomato",
        "disease": "Healthy Foliage",
        "pathogen": "None (Healthy)",
        "symptoms": "Vigorous, dark green foliage with sturdy main stems, uniform leaflets, and healthy blossom clusters.",
        "organic": "Support with steady calcium (bone meal/gypsum) to prevent blossom end rot; mulch heavily around base.",
        "chemical": "No chemical treatment required.",
        "prevention": "Stake plants properly to keep leaves off damp soil; water consistently at soil level."
    }
}

def get_treatment_details(class_name):
    """Retrieve full diagnostic and treatment advice for any class."""
    if class_name in TREATMENT_DATABASE:
        return TREATMENT_DATABASE[class_name]
    
    # Generic fallback
    clean_name = class_name.replace('___', ' - ').replace('_', ' ')
    return {
        "crop": clean_name.split(' - ')[0] if ' - ' in clean_name else "Plant",
        "disease": clean_name.split(' - ')[1] if ' - ' in clean_name else clean_name,
        "pathogen": "Diagnosed condition",
        "symptoms": "Leaf abnormalities, discoloration, or lesions detected by neural vision.",
        "organic": "Apply organic neem oil or broad-spectrum copper soap fungicide.",
        "chemical": "Consult local agricultural extension for registered foliar treatment.",
        "prevention": "Prune affected leaves, avoid wet foliage, and maintain crop rotation."
    }
