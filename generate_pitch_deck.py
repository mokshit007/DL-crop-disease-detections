import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

def create_deck():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6] # Blank slide

    # Color Palette Definitions
    DARK_BG = RGBColor(15, 23, 42)        # Slate 900
    DARK_CARD = RGBColor(30, 41, 59)      # Slate 800
    LIGHT_BG = RGBColor(248, 250, 252)    # Slate 50
    CARD_BG = RGBColor(255, 255, 255)     # White
    CARD_BORDER = RGBColor(226, 232, 240) # Slate 200
    
    PRIMARY_GREEN = RGBColor(5, 150, 105) # Emerald 600
    LIGHT_GREEN = RGBColor(16, 185, 129)  # Emerald 500
    ACCENT_BLUE = RGBColor(37, 99, 235)   # Blue 600
    PURPLE_ACCENT = RGBColor(139, 92, 246)# Violet 500
    WARNING_AMBER = RGBColor(217, 119, 6) # Amber 600
    ALERT_RED = RGBColor(220, 38, 38)     # Red 600
    
    TEXT_DARK = RGBColor(15, 23, 42)      # Slate 900
    TEXT_MUTED = RGBColor(100, 116, 139)  # Slate 500
    TEXT_LIGHT = RGBColor(241, 245, 249)  # Slate 100

    def set_bg(slide, color):
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
        bg.fill.solid()
        bg.fill.fore_color.rgb = color
        bg.line.color.rgb = color
        return bg

    def add_header(slide, category_tag, title_text, dark=False):
        tag_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.7), Inches(0.35))
        tf_tag = tag_box.text_frame
        tf_tag.word_wrap = True
        tf_tag.margin_left = tf_tag.margin_top = tf_tag.margin_right = tf_tag.margin_bottom = 0
        p_tag = tf_tag.paragraphs[0]
        p_tag.text = category_tag.upper()
        p_tag.font.size = Pt(10)
        p_tag.font.bold = True
        p_tag.font.color.rgb = LIGHT_GREEN if dark else PRIMARY_GREEN
        
        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.72), Inches(11.7), Inches(0.6))
        tf_title = title_box.text_frame
        tf_title.word_wrap = True
        tf_title.margin_left = tf_title.margin_top = tf_title.margin_right = tf_title.margin_bottom = 0
        p_title = tf_title.paragraphs[0]
        p_title.text = title_text
        p_title.font.size = Pt(21)
        p_title.font.bold = True
        p_title.font.color.rgb = TEXT_LIGHT if dark else TEXT_DARK

    def create_card(slide, left, top, width, height, bg_color=CARD_BG, border_color=CARD_BORDER):
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
        card.fill.solid()
        card.fill.fore_color.rgb = bg_color
        card.line.color.rgb = border_color
        card.line.width = Pt(1.5)
        return card

    # ==============================================================
    # SLIDE 1: HERO TITLE SLIDE (Dark Theme)
    # ==============================================================
    s1 = prs.slides.add_slide(blank_layout)
    set_bg(s1, DARK_BG)
    
    banner = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(0.8), Inches(2.3), Inches(0.35))
    banner.fill.solid()
    banner.fill.fore_color.rgb = PRIMARY_GREEN
    banner.line.fill.background()
    p_b = banner.text_frame.paragraphs[0]
    p_b.text = "DEEP LEARNING PROTOTYPE"
    p_b.font.size = Pt(9)
    p_b.font.bold = True
    p_b.font.color.rgb = TEXT_LIGHT
    p_b.alignment = PP_ALIGN.CENTER
    
    t_box = s1.shapes.add_textbox(Inches(0.8), Inches(1.3), Inches(11.5), Inches(2.0))
    tf1 = t_box.text_frame
    tf1.word_wrap = True
    p1 = tf1.paragraphs[0]
    p1.text = "Autonomous Crop Disease Detection\n& Plant Pathology AI"
    p1.font.size = Pt(36)
    p1.font.bold = True
    p1.font.color.rgb = TEXT_LIGHT
    
    p2 = tf1.add_paragraph()
    p2.text = "A State-of-the-Art Deep Learning System with Explainable AI & Agronomic Action Plans"
    p2.font.size = Pt(16)
    p2.font.color.rgb = RGBColor(148, 163, 184)
    p2.space_before = Pt(15)

    badges = [
        ("99.94%", "Validation Accuracy", PRIMARY_GREEN),
        ("38 Classes", "14 Crop Species", ACCENT_BLUE),
        ("EfficientNetV2-S", "20.23M Parameters", PURPLE_ACCENT),
        ("Grad-CAM XAI", "Explainable Attention", RGBColor(236, 72, 153))
    ]
    for i, (metric, label, col) in enumerate(badges):
        bx = 0.8 + i * 2.95
        create_card(s1, bx, 3.8, 2.75, 1.6, DARK_CARD, col)
        
        box = s1.shapes.add_textbox(Inches(bx + 0.15), Inches(3.95), Inches(2.45), Inches(1.3))
        tf_b = box.text_frame
        tf_b.word_wrap = True
        
        pm = tf_b.paragraphs[0]
        pm.text = metric
        pm.font.size = Pt(22)
        pm.font.bold = True
        pm.font.color.rgb = col
        
        pl = tf_b.add_paragraph()
        pl.text = label
        pl.font.size = Pt(11)
        pl.font.color.rgb = RGBColor(203, 213, 225)
        pl.space_before = Pt(6)

    f_box = s1.shapes.add_textbox(Inches(0.8), Inches(6.5), Inches(11.5), Inches(0.5))
    tf_f = f_box.text_frame
    pf = tf_f.paragraphs[0]
    pf.text = "Comprehensive Technical Presentation | Automated End-to-End Pipeline Demonstration"
    pf.font.size = Pt(11)
    pf.font.color.rgb = RGBColor(148, 163, 184)

    # ==============================================================
    # SLIDE 2: THE PROBLEM & MOTIVATION
    # ==============================================================
    s2 = prs.slides.add_slide(blank_layout)
    set_bg(s2, LIGHT_BG)
    add_header(s2, "Context & Motivation", "The Challenge: Why Traditional Crop Diagnosis Fails")
    
    cards_s2 = [
        ("01. Global Agricultural Impact", 
         "Up to 40% of global crop yield is lost annually to plant pests and pathogens (FAO estimate).\n\nEarly detection before secondary spread is the single most critical factor in salvaging yields and preventing catastrophic losses for smallholder farmers.", 
         RGBColor(239, 246, 255), ACCENT_BLUE),
        ("02. The Human Agronomist Bottleneck", 
         "Certified plant pathologists are scarce and geographically inaccessible to most remote agricultural regions.\n\nVisual manual inspection is slow, subjective, and prone to misdiagnosis between diseases with visually similar lesions (e.g., Early vs Late Blight).", 
         RGBColor(254, 243, 199), WARNING_AMBER),
        ("03. Where Typical AI Projects Fail", 
         "Most research models remain in isolated Jupyter notebooks with zero usability.\n\nThey act as 'black boxes' without explaining why a decision was reached, provide no actionable remedies to farmers, and hallucinate wild predictions on non-plant images.", 
         RGBColor(254, 242, 242), ALERT_RED)
    ]
    for i, (title, body, bg, border) in enumerate(cards_s2):
        cx = 0.8 + i * 3.95
        create_card(s2, cx, 1.5, 3.75, 5.3, bg, border)
        
        cbox = s2.shapes.add_textbox(Inches(cx + 0.25), Inches(1.75), Inches(3.25), Inches(4.8))
        tf = cbox.text_frame
        tf.word_wrap = True
        
        pt = tf.paragraphs[0]
        pt.text = title
        pt.font.size = Pt(15)
        pt.font.bold = True
        pt.font.color.rgb = border
        
        pb = tf.add_paragraph()
        pb.text = body
        pb.font.size = Pt(11)
        pb.font.color.rgb = TEXT_DARK
        pb.space_before = Pt(14)

    # ==============================================================
    # SLIDE 3: DATASET PIPELINE & SCALE
    # ==============================================================
    s3 = prs.slides.add_slide(blank_layout)
    set_bg(s3, LIGHT_BG)
    add_header(s3, "Data Engineering", "Dataset Scale: 87,000+ Multi-Crop Pathology Images")
    
    data_cards = [
        ("Massive Scale & Volume", "87,000+ labeled leaf specimens automatically scraped and downloaded via KaggleHub API integration, completely removing artificial prototype limits.", PRIMARY_GREEN),
        ("38 Pathological Classes", "Spans 14 commercial crop varieties: Apple, Blueberry, Cherry, Corn, Grape, Orange, Peach, Bell Pepper, Potato, Raspberry, Soybean, Squash, Strawberry, and Tomato.", ACCENT_BLUE),
        ("Full Pathogen Diversity", "Covers complex pathology types: Fungal (Blights, Rusts, Mildews), Bacterial (Spots), Viral (Mosaic, Yellow Leaf Curl), and Arachnid pests (Spider Mites).", WARNING_AMBER),
        ("Stratified Split & Leakage Prevention", "Strict 80% Train, 10% Validation, 10% Test split. Deduplicated image paths ensuring zero data leakage between train and test distributions.", PURPLE_ACCENT)
    ]
    for i, (t, d, col) in enumerate(data_cards):
        col_idx = i % 2
        row_idx = i // 2
        cx = 0.8 + col_idx * 5.9
        cy = 1.5 + row_idx * 2.7
        create_card(s3, cx, cy, 5.7, 2.45, CARD_BG, col)
        
        tb = s3.shapes.add_textbox(Inches(cx + 0.3), Inches(cy + 0.25), Inches(5.1), Inches(1.9))
        tf = tb.text_frame
        tf.word_wrap = True
        
        pt = tf.paragraphs[0]
        pt.text = t
        pt.font.size = Pt(15)
        pt.font.bold = True
        pt.font.color.rgb = col
        
        pd = tf.add_paragraph()
        pd.text = d
        pd.font.size = Pt(11)
        pd.font.color.rgb = TEXT_DARK
        pd.space_before = Pt(8)

    # ==============================================================
    # SLIDE 4: COMPLETE CROP & DISEASE TAXONOMY (14 CROPS, 38 CLASSES)
    # ==============================================================
    s_tax = prs.slides.add_slide(blank_layout)
    set_bg(s_tax, LIGHT_BG)
    add_header(s_tax, "Botanical Pathology Taxonomy", "Supported Agricultural Scope: 14 Crop Species & 38 Pathologies")
    
    taxonomy_groups = [
        ("🍎 Tree & Orchard Fruits", "9 Pathological Classes", [
            "Apple (4 Classes):",
            "  • Apple Scab (Venturia)",
            "  • Black Rot (Botryosphaeria)",
            "  • Cedar Apple Rust (Gymno.)",
            "  • Healthy Apple Foliage",
            "Cherry (2 Classes):",
            "  • Powdery Mildew (Podosphaera)",
            "  • Healthy Cherry Foliage",
            "Peach (2 Classes):",
            "  • Bacterial Spot (Xanthomonas)",
            "  • Healthy Peach Foliage",
            "Blueberry (1 Class):",
            "  • Healthy Blueberry Foliage"
        ], PRIMARY_GREEN),
        ("🌽 Grains, Vines & Citrus", "11 Pathological Classes", [
            "Corn / Maize (4 Classes):",
            "  • Gray Leaf Spot (Cercospora)",
            "  • Common Rust (Puccinia)",
            "  • Northern Leaf Blight (Exsero.)",
            "  • Healthy Corn Foliage",
            "Grape (4 Classes):",
            "  • Black Rot (Guignardia)",
            "  • Esca / Black Measles (Trunk)",
            "  • Leaf Blight (Isariopsis)",
            "  • Healthy Grape Foliage",
            "Orange (1 Class):",
            "  • Citrus Greening (HLB Bacteria)",
            "Bell Pepper (2 Classes):",
            "  • Bacterial Spot (Xanthomonas)",
            "  • Healthy Bell Pepper"
        ], ACCENT_BLUE),
        ("🥔 Tubers, Berries & Row Crops", "8 Pathological Classes", [
            "Potato (3 Classes):",
            "  • Early Blight (Alternaria)",
            "  • Late Blight (Phytophthora)",
            "  • Healthy Potato Foliage",
            "Strawberry (2 Classes):",
            "  • Leaf Scorch (Diplocarpon)",
            "  • Healthy Strawberry Foliage",
            "Squash (1 Class):",
            "  • Powdery Mildew (Podosphaera)",
            "Soybean (1 Class):",
            "  • Healthy Soybean Foliage",
            "Raspberry (1 Class):",
            "  • Healthy Raspberry Foliage"
        ], WARNING_AMBER),
        ("🍅 Flagship Host: Tomato", "10 Pathological Classes", [
            "Tomato (Comprehensive Spectrum):",
            "  • Bacterial Spot (Xanthomonas)",
            "  • Early Blight (Alternaria)",
            "  • Late Blight (Phytophthora)",
            "  • Leaf Mold (Passalora)",
            "  • Septoria Leaf Spot",
            "  • Two-Spotted Spider Mite (Pest)",
            "  • Target Spot (Corynespora)",
            "  • Yellow Leaf Curl Virus (TYLCV)",
            "  • Mosaic Virus (ToMV)",
            "  • Healthy Tomato Foliage"
        ], ALERT_RED)
    ]
    
    for i, (group_title, class_count, items, col) in enumerate(taxonomy_groups):
        cx = 0.8 + i * 2.95
        create_card(s_tax, cx, 1.5, 2.75, 5.3, CARD_BG, col)
        
        tb = s_tax.shapes.add_textbox(Inches(cx + 0.15), Inches(1.68), Inches(2.45), Inches(4.9))
        tf = tb.text_frame
        tf.word_wrap = True
        
        pt = tf.paragraphs[0]
        pt.text = group_title
        pt.font.size = Pt(12)
        pt.font.bold = True
        pt.font.color.rgb = col
        
        pc = tf.add_paragraph()
        pc.text = class_count.upper()
        pc.font.size = Pt(8.5)
        pc.font.bold = True
        pc.font.color.rgb = TEXT_MUTED
        pc.space_before = Pt(2)
        
        for item in items:
            pi = tf.add_paragraph()
            pi.text = item
            if "Classes" in item or "Spectrum" in item:
                pi.font.size = Pt(9.5)
                pi.font.bold = True
                pi.font.color.rgb = TEXT_DARK
                pi.space_before = Pt(4)
            else:
                pi.font.size = Pt(8.5)
                pi.font.color.rgb = RGBColor(51, 65, 85)
                pi.space_before = Pt(1)

    # ==============================================================
    # SLIDE 5: ARCHITECTURE SELECTION
    # ==============================================================
    s4 = prs.slides.add_slide(blank_layout)
    set_bg(s4, LIGHT_BG)
    add_header(s4, "Model Selection", "Why EfficientNetV2-S Outperforms Existing Models")
    
    models_compare = [
        ("ResNet-50 / ResNet-101", 
         "Traditional Standard",
         "- Massive parameter footprint (44.5M - 60M parameters).\n- Uses standard heavy 3x3 convs throughout.\n- Slower training time and prone to early plateau on micro-lesions.\n- High latency on mobile and embedded farm devices.", 
         RGBColor(241, 245, 249), TEXT_MUTED),
        ("Vision Transformers (ViT)", 
         "Attention-Based Standard",
         "- High peak accuracy on massive datasets.\n- Requires 300M+ images (JFT/ImageNet-21k) to avoid overfitting.\n- Lack of inductive bias requires immense training data.\n- Heavy quadratic attention memory footprint; slow inference.", 
         RGBColor(241, 245, 249), TEXT_MUTED),
        ("EfficientNetV2-S (Our Model)", 
         "State-of-the-Art Choice",
         "+ Fused-MBConv Layers: Replaces early depthwise convs, drastically speeding up training.\n+ Training-Aware NAS: Jointly optimizes accuracy, parameter size, and modern GPU throughput.\n+ 52% Fewer Parameters than ResNet-101 (Only 20.23M parameters).\n+ Progressive regularization prevents overfitting on subtle plant textures.", 
         RGBColor(236, 253, 245), PRIMARY_GREEN)
    ]
    for i, (name, tag, details, bg, border) in enumerate(models_compare):
        cx = 0.8 + i * 3.95
        create_card(s4, cx, 1.5, 3.75, 5.3, bg, border)
        
        tb = s4.shapes.add_textbox(Inches(cx + 0.25), Inches(1.75), Inches(3.25), Inches(4.8))
        tf = tb.text_frame
        tf.word_wrap = True
        
        pn = tf.paragraphs[0]
        pn.text = name
        pn.font.size = Pt(14)
        pn.font.bold = True
        pn.font.color.rgb = border if border != TEXT_MUTED else TEXT_DARK
        
        pt = tf.add_paragraph()
        pt.text = tag.upper()
        pt.font.size = Pt(9)
        pt.font.bold = True
        pt.font.color.rgb = border
        pt.space_before = Pt(4)
        
        pd = tf.add_paragraph()
        pd.text = details
        pd.font.size = Pt(10.5)
        pd.font.color.rgb = TEXT_DARK
        pd.space_before = Pt(12)

    # ==============================================================
    # SLIDE 5: ARCHITECTURAL BLUEPRINT (NEW SPEC SLIDE)
    # ==============================================================
    s5 = prs.slides.add_slide(blank_layout)
    set_bg(s5, LIGHT_BG)
    add_header(s5, "Deep Architecture Blueprint", "EfficientNetV2-S: Stage, Layer, Filter & Parameter Specs")
    
    # Left: Parameter & Global Specs Card
    create_card(s5, 0.8, 1.5, 3.6, 5.3, RGBColor(240, 253, 244), PRIMARY_GREEN)
    tb_spec = s5.shapes.add_textbox(Inches(1.0), Inches(1.7), Inches(3.2), Inches(4.8))
    tf_sp = tb_spec.text_frame
    tf_sp.word_wrap = True
    
    p_sp1 = tf_sp.paragraphs[0]
    p_sp1.text = "Model Specifications"
    p_sp1.font.size = Pt(16)
    p_sp1.font.bold = True
    p_sp1.font.color.rgb = PRIMARY_GREEN
    
    spec_items = [
        ("Total Parameters:", "20,226,166 (~20.23M)"),
        ("Trainable Parameters:", "20,226,166 (100%)"),
        ("Input Tensor:", "3 x 224 x 224 (RGB)"),
        ("Feature Head Channels:", "1,280 Filters"),
        ("Output Classes:", "38 Plant Health Categories"),
        ("Convolution Types:", "Fused-MBConv & MBConv + SE"),
        ("Activation Function:", "SiLU (Swish) across all stages"),
        ("Padding Strategy:", "Padding=1 on 3x3 ('Same' pad)\nPadding=0 on 1x1 Projections")
    ]
    for lbl, val in spec_items:
        p_l = tf_sp.add_paragraph()
        p_l.text = f"{lbl} {val}"
        p_l.font.size = Pt(10)
        p_l.font.color.rgb = TEXT_DARK
        p_l.space_before = Pt(6)

    # Right: Stage-by-Stage Table/Grid (Stages 0 to 7 + Head)
    stage_data = [
        ("Stage 0: Stem Conv", "Conv2d 3x3 | Stride 2 | Pad 1", "3 -> 24 Filters", "112 x 112", "1,776"),
        ("Stage 1: Fused-MBConv (2 blk)", "Conv 3x3 + 1x1 | Stride 1 | Pad 1", "24 -> 24 Filters", "112 x 112", "10,464"),
        ("Stage 2: Fused-MBConv (4 blk)", "Conv 3x3 + 1x1 | Stride 2 | Pad 1", "24 -> 48 Filters", "56 x 56", "303,552"),
        ("Stage 3: Fused-MBConv (4 blk)", "Conv 3x3 + 1x1 | Stride 2 | Pad 1", "48 -> 64 Filters", "28 x 28", "589,184"),
        ("Stage 4: MBConv + SE (6 blk)", "Depthwise 3x3 + SE | Stride 2 | Pad 1", "64 -> 128 Filters", "14 x 14", "917,680"),
        ("Stage 5: MBConv + SE (9 blk)", "Depthwise 3x3 + SE | Stride 1 | Pad 1", "128 -> 160 Filters", "14 x 14", "3,463,840"),
        ("Stage 6: MBConv + SE (15 blk)", "Depthwise 3x3 + SE | Stride 2 | Pad 1", "160 -> 256 Filters", "7 x 7", "14,561,832"),
        ("Stage 7: Head Conv", "Conv2d 1x1 | Stride 1 | Pad 0", "256 -> 1,280 Filters", "7 x 7", "330,240"),
        ("Classifier Head", "AdaptiveAvgPool2d + Dropout(0.2) + Linear", "1,280 -> 38 Classes", "1 x 1", "48,678")
    ]
    
    # Render table rows as structured mini-cards
    for r_idx, (stg, op, flt, res, prm) in enumerate(stage_data):
        ry = 1.5 + r_idx * 0.58
        bg_col = CARD_BG if r_idx % 2 == 0 else RGBColor(241, 245, 249)
        create_card(s5, 4.6, ry, 7.9, 0.52, bg_col, CARD_BORDER)
        
        tb_row = s5.shapes.add_textbox(Inches(4.7), Inches(ry + 0.05), Inches(7.7), Inches(0.42))
        tf_r = tb_row.text_frame
        tf_r.word_wrap = True
        
        pr = tf_r.paragraphs[0]
        pr.text = f"{stg}   |   {op}   |   {flt}   |   Res: {res}   |   Params: {prm}"
        pr.font.size = Pt(9.5)
        pr.font.color.rgb = TEXT_DARK
        if "Head" in stg or "Classifier" in stg or "Stem" in stg:
            pr.font.bold = True
            pr.font.color.rgb = PRIMARY_GREEN if "Classifier" in stg else ACCENT_BLUE

    # ==============================================================
    # SLIDE 6: FEATURE ANALYSIS MECHANISM (NEW MECHANISM SLIDE)
    # ==============================================================
    s6 = prs.slides.add_slide(blank_layout)
    set_bg(s6, LIGHT_BG)
    add_header(s6, "Hierarchical Feature Extraction", "How EfficientNetV2 Analyzes Botanical Leaf Pathology")
    
    analysis_steps = [
        ("Level 1: Low-Level Morphology", 
         "Stages 0 to 2 (Stem & Shallow Fused-MBConv)",
         "Filters detect primary botanical boundaries: leaf contour, healthy chlorophyll green gradients, petiole stems, and boundary separation from background surfaces.\n\nFilters operate at high resolution (112x112 down to 56x56) preserving fine structural edges.",
         PRIMARY_GREEN),
        ("Level 2: Mid-Level Texture & Chlorosis", 
         "Stages 3 to 4 (Fused-MBConv & MBConv + SE)",
         "Detects leaf venation networks, surface roughness, interveinal chlorosis (yellowing), and early necrotic flecks.\n\nResolution reduces to 28x28 and 14x14 while channel depth expands to 64 and 128 filters.",
         ACCENT_BLUE),
        ("Level 3: High-Level Pathological Lesions", 
         "Stages 5 to 6 (Deep MBConv with Squeeze-and-Excitation)",
         "Learns intricate disease signatures: concentric bullseye rings of Early Blight, fuzzy oomycete sporangia of Late Blight, powdery mildew talcum blankets, and leaf scorch margins.\n\n15 blocks in Stage 6 extract highly abstract visual representations at 7x7 spatial grid.",
         WARNING_AMBER),
        ("Level 4: Squeeze-and-Excitation Attention", 
         "Channel-Wise Feature Recalibration",
         "SE blocks dynamically weight each channel: they automatically amplify feature maps containing lesion signals while suppressing irrelevant healthy leaf tissue.\n\nFollowed by Global Average Pooling (1280-D vector) and Softmax projection over 38 classes.",
         PURPLE_ACCENT)
    ]
    for i, (t, sub, desc, col) in enumerate(analysis_steps):
        cx = 0.8 + i * 2.95
        create_card(s6, cx, 1.5, 2.75, 5.3, CARD_BG, col)
        
        tb = s6.shapes.add_textbox(Inches(cx + 0.2), Inches(1.7), Inches(2.35), Inches(4.8))
        tf = tb.text_frame
        tf.word_wrap = True
        
        pt = tf.paragraphs[0]
        pt.text = t
        pt.font.size = Pt(13)
        pt.font.bold = True
        pt.font.color.rgb = col
        
        ps = tf.add_paragraph()
        ps.text = sub
        ps.font.size = Pt(9.5)
        ps.font.bold = True
        ps.font.color.rgb = TEXT_MUTED
        ps.space_before = Pt(3)
        
        pd = tf.add_paragraph()
        pd.text = desc
        pd.font.size = Pt(10)
        pd.font.color.rgb = TEXT_DARK
        pd.space_before = Pt(10)

    # ==============================================================
    # SLIDE 7: SOTA TRAINING ENGINEERING
    # ==============================================================
    s7 = prs.slides.add_slide(blank_layout)
    set_bg(s7, LIGHT_BG)
    add_header(s7, "Deep Learning Techniques", "Advanced Training Engineering: 4 SOTA Pillars")
    
    pillars = [
        ("01. Automatic Mixed Precision (AMP)", 
         "Utilized torch.amp.autocast and GradScaler with FP16 math on GPU Tensor Cores.", 
         "Cuts memory consumption in half and accelerates training speed by 2.2x without precision loss.", 
         PRIMARY_GREEN),
        ("02. OneCycleLR Super-Convergence", 
         "Dynamic learning rate that ramps up to 1e-3 before cosine-decaying down over epochs.", 
         "Allows the model to rapidly jump over sharp local minima and settle in a robust, wide basin.", 
         ACCENT_BLUE),
        ("03. Label Smoothing Regularization", 
         "Softened hard ground-truth targets (1.0 -> 0.9) with smoothing factor = 0.1.", 
         "Directly prevents the network from becoming overconfident, dramatically boosting test generalization.", 
         PURPLE_ACCENT),
        ("04. AdamW & Advanced Augmentations", 
         "Decoupled weight decay (1e-4) alongside ColorJitter, Random Flips, and Resized Crops.", 
         "Forces the network to learn true morphological leaf features rather than lighting or studio artifacts.", 
         WARNING_AMBER)
    ]
    for i, (t, sub, impact, col) in enumerate(pillars):
        col_idx = i % 2
        row_idx = i // 2
        cx = 0.8 + col_idx * 5.9
        cy = 1.5 + row_idx * 2.7
        create_card(s7, cx, cy, 5.7, 2.45, CARD_BG, col)
        
        tb = s7.shapes.add_textbox(Inches(cx + 0.3), Inches(cy + 0.2), Inches(5.1), Inches(2.0))
        tf = tb.text_frame
        tf.word_wrap = True
        
        pt = tf.paragraphs[0]
        pt.text = t
        pt.font.size = Pt(14)
        pt.font.bold = True
        pt.font.color.rgb = col
        
        ps = tf.add_paragraph()
        ps.text = sub
        ps.font.size = Pt(10)
        ps.font.color.rgb = TEXT_DARK
        ps.space_before = Pt(4)
        
        pi = tf.add_paragraph()
        pi.text = f"Impact: {impact}"
        pi.font.size = Pt(10)
        pi.font.bold = True
        pi.font.color.rgb = PRIMARY_GREEN
        pi.space_before = Pt(6)

    # ==============================================================
    # SLIDE 8: RESULTS & TRAINING CURVES
    # ==============================================================
    s8 = prs.slides.add_slide(blank_layout)
    set_bg(s8, LIGHT_BG)
    add_header(s8, "Empirical Validation", "Training Results: 99.94% Validation Accuracy")
    
    chart_path = 'results/sota_training_curves.png'
    if os.path.exists(chart_path):
        s8.shapes.add_picture(chart_path, Inches(0.8), Inches(1.5), Inches(7.5), Inches(5.3))
    else:
        create_card(s8, 0.8, 1.5, 7.5, 5.3, CARD_BG, CARD_BORDER)

    results_stats = [
        ("99.94%", "Peak Validation Accuracy", "Recorded at Epoch 10 across 38 diverse classes.", PRIMARY_GREEN),
        ("0.6748", "Final Validation Loss", "Steady decline demonstrating smooth convergence.", ACCENT_BLUE),
        ("Super-Fast Convergence", "Hit 99.20% by Epoch 4", "OneCycleLR enabled lightning-fast learning.", PURPLE_ACCENT)
    ]
    for j, (val, title, desc, col) in enumerate(results_stats):
        cy = 1.5 + j * 1.8
        create_card(s8, 8.6, cy, 3.9, 1.6, CARD_BG, col)
        
        tb = s8.shapes.add_textbox(Inches(8.8), Inches(cy + 0.15), Inches(3.5), Inches(1.3))
        tf = tb.text_frame
        tf.word_wrap = True
        
        pv = tf.paragraphs[0]
        pv.text = val
        pv.font.size = Pt(20)
        pv.font.bold = True
        pv.font.color.rgb = col
        
        pt = tf.add_paragraph()
        pt.text = title
        pt.font.size = Pt(11)
        pt.font.bold = True
        pt.font.color.rgb = TEXT_DARK
        pt.space_before = Pt(2)
        
        pd = tf.add_paragraph()
        pd.text = desc
        pd.font.size = Pt(9.5)
        pd.font.color.rgb = TEXT_MUTED

    # ==============================================================
    # SLIDE 9: EXPLAINABLE AI (GRAD-CAM)
    # ==============================================================
    s9 = prs.slides.add_slide(blank_layout)
    set_bg(s9, LIGHT_BG)
    add_header(s9, "Explainable AI (XAI)", "Grad-CAM: Transparent Botanical Attention Heatmaps")
    
    gcam_path = 'results/gradcam_demo.png'
    if os.path.exists(gcam_path):
        s9.shapes.add_picture(gcam_path, Inches(0.8), Inches(1.5), Inches(6.8), Inches(5.3))
    else:
        create_card(s9, 0.8, 1.5, 6.8, 5.3, CARD_BG, CARD_BORDER)
        
    gcam_points = [
        ("The 'Black Box' Agronomy Dilemma", 
         "Farmers and agricultural extension officers will not trust an AI that outputs a blind label. They need to verify that the model looked at actual diseased leaf tissue rather than background noise.", 
         TEXT_DARK),
        ("How Our Grad-CAM Hooks Work", 
         "We register PyTorch backward hooks on the final convolutional layer (model.features[-1]). Gradients flow backwards to compute importance weights for each feature activation map.", 
         ACCENT_BLUE),
        ("Clinical Lesion Localization", 
         "Applies ReLU and bilinear upsampling to generate an intuitive red/yellow heat overlay directly pointing to leaf spots, scorch margins, and fungal spore patches.", 
         PRIMARY_GREEN)
    ]
    for k, (title, desc, col) in enumerate(gcam_points):
        cy = 1.5 + k * 1.8
        create_card(s9, 7.9, cy, 4.6, 1.6, CARD_BG, CARD_BORDER)
        
        tb = s9.shapes.add_textbox(Inches(8.1), Inches(cy + 0.15), Inches(4.2), Inches(1.3))
        tf = tb.text_frame
        tf.word_wrap = True
        
        pt = tf.paragraphs[0]
        pt.text = title
        pt.font.size = Pt(13)
        pt.font.bold = True
        pt.font.color.rgb = col
        
        pd = tf.add_paragraph()
        pd.text = desc
        pd.font.size = Pt(9.5)
        pd.font.color.rgb = TEXT_DARK
        pd.space_before = Pt(4)

    # ==============================================================
    # SLIDE 10: PRODUCTION WEB APPLICATION & REMEDIES
    # ==============================================================
    s10 = prs.slides.add_slide(blank_layout)
    set_bg(s10, LIGHT_BG)
    add_header(s10, "Deployment & UX", "CropSense AI: End-to-End Field-Ready Web Platform")
    
    prod_cards = [
        ("1. Live Field Camera Input", 
         "Integrated st.camera_input allowing real-time photo capture from farmers' mobile phones or tablets directly in the field alongside disk upload.", 
         CARD_BG, PRIMARY_GREEN),
        ("2. Actionable Agronomic Remedies", 
         "Built-in pathology database: Provides causative pathogen identification, organic controls (Neem, Bacillus), chemical sprays, and cultural prevention.", 
         CARD_BG, ACCENT_BLUE),
        ("3. Quality & Multi-Leaf Gatekeeper", 
         "Advanced morphological contour segmentation detects and rejects non-plant images and multiple-leaf clusters with an explicit warning: 'Something is wrong with the uploaded image', guiding users to isolated single leaves.", 
         CARD_BG, WARNING_AMBER),
        ("4. Instant Diagnostic PDF Reports", 
         "One-click compilation of an official PDF report with original leaf photos, Grad-CAM heatmaps, confidence charts, and prescription steps.", 
         CARD_BG, PURPLE_ACCENT)
    ]
    for i, (t, b, bg, col) in enumerate(prod_cards):
        cx = 0.8 + i * 2.95
        create_card(s10, cx, 1.5, 2.75, 5.3, bg, col)
        
        tb = s10.shapes.add_textbox(Inches(cx + 0.2), Inches(1.7), Inches(2.35), Inches(4.8))
        tf = tb.text_frame
        tf.word_wrap = True
        
        pt = tf.paragraphs[0]
        pt.text = t
        pt.font.size = Pt(13)
        pt.font.bold = True
        pt.font.color.rgb = col
        
        pb = tf.add_paragraph()
        pb.text = b
        pb.font.size = Pt(10.5)
        pb.font.color.rgb = TEXT_DARK
        pb.space_before = Pt(12)

    # ==============================================================
    # SLIDE 11: WHAT IS GOOD (STRENGTHS)
    # ==============================================================
    s11 = prs.slides.add_slide(blank_layout)
    set_bg(s11, LIGHT_BG)
    add_header(s11, "Project Highlights", "What is GOOD in This Project (Key Strengths)")
    
    strengths = [
        ("Exceptional Diagnostic Accuracy", 
         "Achieved 99.94% validation accuracy across 38 categories, matching or exceeding published academic benchmarks on the New Plant Diseases Dataset.", 
         PRIMARY_GREEN),
        ("Full-Stack Actionability", 
         "Not merely an abstract research classifier. Delivers immediate value to end-users via organic/chemical treatments and downloadable PDF agronomy reports.", 
         PRIMARY_GREEN),
        ("Transparent & Trustworthy (XAI)", 
         "Grad-CAM visual overlays remove the black-box stigma, allowing growers and agricultural inspectors to visually confirm where disease symptoms lie.", 
         PRIMARY_GREEN),
        ("Modern & Efficient Engineering", 
         "Utilizes EfficientNetV2-S with AMP (FP16) and OneCycleLR, resulting in a lightweight 20.23M parameter model capable of fast, sub-second inference.", 
         PRIMARY_GREEN)
    ]
    for i, (t, d, col) in enumerate(strengths):
        col_idx = i % 2
        row_idx = i // 2
        cx = 0.8 + col_idx * 5.9
        cy = 1.5 + row_idx * 2.7
        create_card(s11, cx, cy, 5.7, 2.45, RGBColor(240, 253, 244), col)
        
        tb = s11.shapes.add_textbox(Inches(cx + 0.3), Inches(cy + 0.2), Inches(5.1), Inches(2.0))
        tf = tb.text_frame
        tf.word_wrap = True
        
        pt = tf.paragraphs[0]
        pt.text = f"[+] {t}"
        pt.font.size = Pt(15)
        pt.font.bold = True
        pt.font.color.rgb = col
        
        pd = tf.add_paragraph()
        pd.text = d
        pd.font.size = Pt(11)
        pd.font.color.rgb = TEXT_DARK
        pd.space_before = Pt(8)

    # ==============================================================
    # SLIDE 12: WHAT IS BAD (HONEST LIMITATIONS)
    # ==============================================================
    s12 = prs.slides.add_slide(blank_layout)
    set_bg(s12, LIGHT_BG)
    add_header(s12, "Critical Evaluation", "What is BAD in This Project (Honest Limitations)")
    
    limitations = [
        ("Controlled Background Bias", 
         "Most training images have uniform laboratory/neutral backgrounds. In dense wild fields with complex backgrounds (soil, weeds, shadows), accuracy can degrade.", 
         ALERT_RED),
        ("Single-Leaf Close-Up Constraint", 
         "The model requires an isolated, centered leaf image. It cannot currently scan an entire orchard tree canopy or field from drone/aerial imagery.", 
         ALERT_RED),
        ("Closed-World Taxonomy", 
         "Though protected by our color heuristic, the network still maps any botanical leaf to its 38 classes. Unseen crops (e.g., Mango, Rice) will be forced to the closest match.", 
         WARNING_AMBER),
        ("Single-Disease Assumption (No Co-Infections)", 
         "Plants often suffer simultaneous multi-pathogen attacks (e.g., Mites + Early Blight). The model is single-label multi-class, predicting only the dominant symptom.", 
         WARNING_AMBER)
    ]
    for i, (t, d, col) in enumerate(limitations):
        col_idx = i % 2
        row_idx = i // 2
        cx = 0.8 + col_idx * 5.9
        cy = 1.5 + row_idx * 2.7
        create_card(s12, cx, cy, 5.7, 2.45, RGBColor(254, 242, 242), col)
        
        tb = s12.shapes.add_textbox(Inches(cx + 0.3), Inches(cy + 0.2), Inches(5.1), Inches(2.0))
        tf = tb.text_frame
        tf.word_wrap = True
        
        pt = tf.paragraphs[0]
        pt.text = f"[-] {t}"
        pt.font.size = Pt(15)
        pt.font.bold = True
        pt.font.color.rgb = col
        
        pd = tf.add_paragraph()
        pd.text = d
        pd.font.size = Pt(11)
        pd.font.color.rgb = TEXT_DARK
        pd.space_before = Pt(8)

    # ==============================================================
    # SLIDE 13: FUTURE SCOPE & ROADMAP
    # ==============================================================
    s13 = prs.slides.add_slide(blank_layout)
    set_bg(s13, LIGHT_BG)
    add_header(s13, "Engineering Roadmap", "Future Improvements: Evolving to Industrial AgTech")
    
    roadmap = [
        ("1. Object Detection (YOLOv10)", 
         "Transition from image classification to bounding-box object detection. Allows farmers to point their camera at a whole plant and simultaneously detect multiple diseased leaves with severity counting.", 
         ACCENT_BLUE),
        ("2. Edge Quantization (INT8 / ONNX)", 
         "Quantize model weights to 8-bit integers and export to ONNX/TensorRT. Enables true offline execution on low-cost Android phones with zero internet connection in remote farmlands.", 
         PRIMARY_GREEN),
        ("3. Multimodal Agronomist Assistant", 
         "Integrate small language models (SLMs) to allow conversational agronomic follow-ups ('How often should I apply copper spray if it rains tomorrow?').", 
         PURPLE_ACCENT)
    ]
    for i, (t, d, col) in enumerate(roadmap):
        cx = 0.8 + i * 3.95
        create_card(s13, cx, 1.5, 3.75, 5.3, CARD_BG, col)
        
        tb = s13.shapes.add_textbox(Inches(cx + 0.25), Inches(1.75), Inches(3.25), Inches(4.8))
        tf = tb.text_frame
        tf.word_wrap = True
        
        pt = tf.paragraphs[0]
        pt.text = t
        pt.font.size = Pt(15)
        pt.font.bold = True
        pt.font.color.rgb = col
        
        pd = tf.add_paragraph()
        pd.text = d
        pd.font.size = Pt(11)
        pd.font.color.rgb = TEXT_DARK
        pd.space_before = Pt(14)

    # ==============================================================
    # SLIDE 14: CONCLUSION & LIVE DEMO (Dark Theme)
    # ==============================================================
    s14 = prs.slides.add_slide(blank_layout)
    set_bg(s14, DARK_BG)
    add_header(s14, "Summary & Demo", "Project Conclusion & Live Demonstration", dark=True)
    
    create_card(s14, 0.8, 1.5, 6.8, 5.3, DARK_CARD, PRIMARY_GREEN)
    tb_c = s14.shapes.add_textbox(Inches(1.1), Inches(1.75), Inches(6.2), Inches(4.8))
    tf_c = tb_c.text_frame
    tf_c.word_wrap = True
    
    p_ct = tf_c.paragraphs[0]
    p_ct.text = "Summary of Deliverables"
    p_ct.font.size = Pt(18)
    p_ct.font.bold = True
    p_ct.font.color.rgb = LIGHT_GREEN
    
    summary_bullets = [
        "Delivered a complete, functioning SOTA crop pathology platform.",
        "87,000+ images trained across 38 disease & healthy categories.",
        "EfficientNetV2-S achieved 99.94% accuracy with AMP & OneCycleLR.",
        "Detailed architecture specs: 20.23M parameters, Fused-MBConv & SE attention.",
        "Explainable AI via Grad-CAM eliminates black-box guesswork.",
        "Full web app with live camera capture & downloadable PDF prescriptions.",
        "Honest assessment of background bias and single-leaf constraints documented."
    ]
    for b in summary_bullets:
        pb = tf_c.add_paragraph()
        pb.text = f"- {b}"
        pb.font.size = Pt(11.5)
        pb.font.color.rgb = RGBColor(226, 232, 240)
        pb.space_before = Pt(7)

    create_card(s14, 7.9, 1.5, 4.6, 5.3, DARK_CARD, ACCENT_BLUE)
    tb_d = s14.shapes.add_textbox(Inches(8.2), Inches(1.75), Inches(4.0), Inches(4.8))
    tf_d = tb_d.text_frame
    tf_d.word_wrap = True
    
    p_dt = tf_d.paragraphs[0]
    p_dt.text = "Ready for Live Demo"
    p_dt.font.size = Pt(18)
    p_dt.font.bold = True
    p_dt.font.color.rgb = RGBColor(96, 165, 250)
    
    demo_lines = [
        "Application Command:",
        "streamlit run app.py",
        "Local Server URL:",
        "http://localhost:8501",
        "\nThank you for your attention!",
        "Now open for questions & live leaf diagnosis."
    ]
    for dl in demo_lines:
        pdl = tf_d.add_paragraph()
        pdl.text = dl
        if "streamlit" in dl or "http" in dl:
            pdl.font.size = Pt(13)
            pdl.font.bold = True
            pdl.font.color.rgb = LIGHT_GREEN
        elif "Thank" in dl:
            pdl.font.size = Pt(14)
            pdl.font.bold = True
            pdl.font.color.rgb = TEXT_LIGHT
            pdl.space_before = Pt(14)
        else:
            pdl.font.size = Pt(11)
            pdl.font.color.rgb = RGBColor(148, 163, 184)
            pdl.space_before = Pt(4)

    output_filename = "CropSense_AI_Official_Presentation.pptx"
    prs.save(output_filename)
    print(f"Updated {output_filename} with full architectural blueprint successfully!")

if __name__ == '__main__':
    create_deck()
