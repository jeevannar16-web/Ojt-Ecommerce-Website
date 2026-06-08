"""
generate_fixtures.py
--------------------
Run this script to produce `store_data.json` – a Django fixture that loads
17 categories and 340 products (20 per category) into the database.
"""

import json
import random

# ---------------------------------------------------------------------------
# Category definitions
# ---------------------------------------------------------------------------
CATEGORIES = [
    (1,  "Cardio Training"),
    (2,  "Wearable Tech"),
    (3,  "Yoga & Pilates"),
    (4,  "Weight Loss"),
    (5,  "Muscle & Strength"),
    (6,  "Supplements & Nutrition"),
    (7,  "Recovery & Wellness"),
    (8,  "Mobility Training"),
    (9,  "Outdoor Adventure"),
    (10, "Sleep Optimization"),
    (11, "Kettlebell Workouts"),
    (12, "Activewear Clothing"),
    (13, "Bodyweight Calisthenics"),
    (14, "Dumbbell Training"),
    (15, "Resistance Bands"),
    (16, "Gym Machines"),
    (17, "Hydration Systems"),
]

# ---------------------------------------------------------------------------
# Product names per category (20 per category)
# ---------------------------------------------------------------------------
PRODUCT_NAMES = {
    1: [
        "Pro Treadmill 3000", "Folding Treadmill Lite", "Incline Trainer X5",
        "Elliptical Cross-Trainer", "Air Bike Elite", "Rowing Machine Pro",
        "Stair Climber 500", "Spin Bike Studio", "Compact Cardio Stepper",
        "Recumbent Bike Classic", "Cardio Glider Plus", "Smart Treadmill T10",
        "Under-Desk Bike Pedaller", "Curved Manual Treadmill", "Cross-Country Ski Machine",
        "Cardio Jump Rope Pro", "Mini Trampoline Rebounder", "Heart Rate Monitor",
        "Treadmill Safety Key", "Speed Ladder Agility Kit",
    ],
    2: [
        "Alpha Fitness Watch", "HRV Recovery Band", "Smart Ring Fitness Pro",
        "GPS Running Watch Lite", "Swim-Proof Sport Watch", "ECG Smartwatch Elite",
        "Pulse Ox Wristband", "Kids Activity Tracker", "Slim Calorie Counter Band",
        "Adventure GPS Tracker", "Golfer GPS Watch", "Cycling Computer GPS",
        "Body Temperature Patch", "Smart Posture Corrector", "Hydration Monitor Patch",
        "EMS Muscle Stimulator", "Running Footpod Sensor", "Smart Jump Rope Counter",
        "Lactate Threshold Monitor", "VO2 Max Estimator Watch",
    ],
    3: [
        "Premium Yoga Mat 6mm", "Travel Yoga Mat Ultra-Thin", "Cork Yoga Block Set",
        "Yoga Strap 8ft Organic", "Pilates Reformer Beginner", "Pilates Magic Circle",
        "Yoga Bolster Rectangular", "Round Meditation Cushion", "Acupressure Mat & Pillow",
        "Yoga Wheel 12-Inch", "Resistance Loop Bands Yoga", "Balance Board Yoga",
        "Yoga Socks Non-Slip Grip", "Inversion Yoga Swing", "Yoga Sandbag Adjustable",
        "Pilates Resistance Ring", "Yoga Fitness Ball 65cm", "Hot Yoga Towel Microfibre",
        "Meditation Singing Bowl", "Aromatherapy Yoga Kit",
    ],
    4: [
        "Smart Body Scale Wi-Fi", "Calorie Counting Food Scale", "Meal Prep Container Set",
        "Portion Control Plate", "Fat-Burning Cardio Plan", "Intermittent Fasting Timer",
        "Waist Trimmer Belt Neo", "Body Tape Measure Pro", "Resistance Band Workout Set",
        "Jump Rope Speed 3mm", "HIIT Timer App Annual", "Low-Calorie Recipe Book",
        "Green Tea Fat Burner", "CLA Supplement 1000mg", "Whey Protein Lean Blend",
        "Collagen Peptides Powder", "Glucomannan Capsules", "Apple Cider Vinegar Gummies",
        "Metabolism Boost Tea", "Sleep Aid Melatonin 5mg",
    ],
    5: [
        "Olympic Barbell 20kg", "Weight Plate Set 100kg", "Power Rack Full Cage",
        "Flat Weight Bench", "Adjustable FID Bench", "Hex Trap Bar Deadlift",
        "EZ Curl Bar 47-Inch", "Tricep Rope Attachment", "Lat Pulldown Bar",
        "Preacher Curl Bench", "Dip Bar Station", "Gymnastic Rings Wood 28mm",
        "Wrist Wraps Strength", "Lifting Straps Cotton Pair", "Powerlifting Belt 10mm",
        "Knee Sleeves 7mm Pair", "Elbow Sleeves 5mm Pair", "Chalk Block Gym Grade",
        "Deadlift Socks", "Pre-Workout Strength Formula",
    ],
    6: [
        "Whey Protein 2.5kg Choc", "Plant Protein Vanilla 1kg", "Casein Protein Midnight",
        "Creatine HCl Caps 750mg", "Beta-Alanine 200g Powder", "Citrulline Malate 2:1",
        "L-Glutamine Recovery 400g", "Fish Oil Omega-3 3000mg", "Magnesium Glycinate 400mg",
        "Vitamin D3 5000IU", "Zinc Picolinate 30mg", "Ashwagandha KSM-66 600mg",
        "Rhodiola Rosea 500mg", "Caffeine L-Theanine Stack", "Electrolyte Tablets x60",
        "Greens Superfood Powder", "Digestive Enzyme Complex", "Probiotic 50 Billion CFU",
        "Collagen Marine Peptides", "HMB Capsules 1000mg",
    ],
    7: [
        "Percussive Massage Gun", "Vibrating Foam Roller", "Cold Therapy Ice Pack Set",
        "Infrared Heating Pad Large", "Compression Recovery Socks", "Epsom Salt Bath Soak 5kg",
        "Acupuncture Massage Mat", "TENS Unit Muscle Stimulator", "Trigger Point Massage Ball",
        "Mobility Stick Roller", "Stretching Strap Loop", "Recovery Compression Sleeves",
        "Sleep Eye Mask Contoured", "White Noise Sleep Machine", "Magnesium Spray Transdermal",
        "CBD Recovery Cream 1000mg", "Cryotherapy Cryo Sleeve", "Warm Mist Humidifier",
        "Pulse Ox Recovery Monitor", "HRV Recovery App Annual",
    ],
    8: [
        "Hip Flexor Stretch Kit", "Thoracic Spine Roller", "Ankle Mobility Band",
        "Shoulder Mobility Stick", "Deep Squat Support Block", "Mobility Flow Programme",
        "Hip Circle Resistance Band", "Spinal Decompression Bar", "Peanut Massage Ball",
        "Stretching Wedge Set", "Mobility E-Book", "Active Stretching Programme",
        "Rotator Cuff Rehab Kit", "Kneeling Pad Mobility Mat", "Doorframe Pull-Up Bar",
        "Lacrosse Ball 3-Pack", "Mobility Snake Roller", "Wrist Mobility Trainer",
        "Piriformis Stretch Cushion", "Hip Distraction Loop Band",
    ],
    9: [
        "Trail Running Hydration Vest", "Trekking Poles Carbon Pair", "All-Terrain Trail Shoes",
        "Hiking GPS Navigator", "Emergency Bivvy Bag", "Multi-Tool Outdoor 14-in-1",
        "Lightweight Backpack 45L", "Collapsible Water Filter", "Headlamp 500 Lumen",
        "Navigation Compass Silva", "Packable Down Jacket 800 Fill", "Waterproof Hiking Gaiters",
        "Bear Canister 700 cu in", "Lightweight Sleeping Bag -5°C", "Ultralight Trekking Tent 2P",
        "Paracord 550 100ft", "Trail Camera Motion Sensor", "Solar Charger Panel 20W",
        "Satellite Communicator Device", "Trekking Sandal Sport",
    ],
    10: [
        "Weighted Blanket 15lb", "Contour Memory Foam Pillow", "White Noise Machine Pro",
        "Sleep Tracking Smart Mat", "Sunrise Alarm Clock", "Blackout Curtain Liners",
        "Melatonin 5mg Fast Dissolve", "Magnesium Bisglycinate Sleep", "Cooling Mattress Topper",
        "Blue Light Blocking Glasses", "Sleep Coaching App Premium", "Guided Sleep Meditation Set",
        "Lavender Essential Oil 30ml", "Aromatherapy Diffuser", "Sleep Sound Earplugs",
        "Eye Mask Silk Contoured", "Sleep Restriction Workbook", "Temperature Regulating Duvet",
        "Pillow Protector Waterproof", "Adjustable Bed Wedge Pillow",
    ],
    11: [
        "Cast Iron Kettlebell 8kg", "Vinyl Dipped Kettlebell 12kg", "Competition Kettlebell 16kg",
        "Adjustable Kettlebell 6-32kg", "Kettlebell 24kg Pro", "Kettlebell 32kg Power",
        "Double Kettlebell Set 2×16kg", "Kettlebell Training Manual", "Kettlebell Swing Target Mat",
        "Hardstyle KB Programme 12wk", "Kettlebell Sport Gloves", "KB Handle Barbell Adapter",
        "Kettlebell Chalk Bowl", "Wrist Guard KB Set", "Forearm Protector Sleeves",
        "Grip Aid Liquid Chalk", "Kettlebell Rack Stand 2-Tier", "KB Conditioning Programme",
        "Swing Counter App", "Enter the Kettlebell Book",
    ],
    12: [
        "Compression Tights Men", "High-Waist Leggings Women", "Athletic Performance Tee",
        "Racerback Sports Bra", "High-Impact Sports Bra", "Running Shorts 5-Inch",
        "Gym Shorts 9-Inch", "Training Tank Top", "Full-Zip Hoodie Fleece",
        "Lightweight Running Jacket", "Thermal Base Layer Top", "Thermal Base Layer Bottoms",
        "Athletic Polo Shirt", "Swim Performance Jammers", "Training Gloves Half-Finger",
        "CrossFit Nano Shoe", "Running Sock Cushion 3-Pack", "Compression Calf Sleeves",
        "Athletic Headband Wide", "Sweat-Wicking Cap Running",
    ],
    13: [
        "Pull-Up Bar Doorframe", "Parallel Bar Dip Station", "Push-Up Board Multi-Angle",
        "Gymnastic Rings 28mm", "Calisthenics Parallettes Low", "Calisthenics Parallettes High",
        "Resistance Band Pull-Up Assist", "Ab Wheel Rollout Trainer", "Suspension Trainer Straps",
        "Power Tower Home Station", "Calisthenics Beginner Book", "Handstand Training Course",
        "L-Sit Progression Guide", "Planche Lean Blocks", "Iron Cross Conditioning Plan",
        "Front Lever Mastery Course", "Muscle-Up Tutorial Series", "Calisthenics Nutrition Guide",
        "Wrist Wraps Calisthenics", "Horizontal Bar Outdoor",
    ],
    14: [
        "Adjustable Dumbbell Set 5-52lb", "Hex Dumbbell 10kg Pair", "Neoprene Dumbbell Set 1-5kg",
        "Chrome Dumbbell Pair 20kg", "Dumbbell Storage Rack 3-Tier", "Rubber Hex Dumbbell 25kg",
        "Adjustable Dumbbell 10-90lb", "Dumbbell Workout Book", "Dumbbell Training App Annual",
        "DB Flat Press Bench", "Dumbbell Curl Bar Handle", "Foam Pad Dumbbell Kneeling",
        "DB Romanian Deadlift Guide", "Dumbbell Circuit Workout Cards", "DB Lateral Raise Cable Handle",
        "Dumbbell Shoulder Press Stand", "Rubber Dumbbell 15kg Pair", "DB Functional Training Manual",
        "Dumbbell Wrist Roller Pair", "Powerblock Elite Upgrade Kit",
    ],
    15: [
        "Loop Band Set 5 Levels", "Therapy Band 6m Roll", "Heavy Duty Pull-Up Band 200lb",
        "Compact Travel Band Kit", "Fabric Glute Band Set", "Resistance Tube Set Handles",
        "Band Bar Squat Attachment", "Mini Band Hip Circle Set", "Ankle Cuff Band Attachment",
        "Door Anchor Band Set", "Wall Anchor Plate Steel", "Band-Only Upper Body Plan",
        "Band-Only Lower Body Plan", "Full Body Band Programme", "Resistance Band Book",
        "Band Tension Chart Poster", "Quick-Release Carabiner Set", "Lat Pull-Down Band Kit",
        "Hip Thrust Band Platform", "Band Deadlift Protocol",
    ],
    16: [
        "Smith Machine Home Gym", "Functional Trainer Cable", "Lat Pulldown Machine",
        "Leg Press Machine", "Chest Press Machine Selectorised", "Seated Row Machine",
        "Shoulder Press Selectorised", "Leg Extension Machine", "Leg Curl Seated Machine",
        "Leg Curl Prone Machine", "Pec Deck Fly Machine", "Cable Row Low Pulley",
        "Assisted Dip Pull-Up Machine", "Abdominal Crunch Machine", "Glute Kickback Machine",
        "Hip Abduction Machine", "Back Extension Roman Chair", "Multi-Jungle Cable Tower",
        "Hack Squat Machine", "V-Squat Machine",
    ],
    17: [
        "Insulated Water Bottle 1L", "Hydration Pack 2L Bladder", "Smart Hydration Bottle LED",
        "Collapsible Water Bottle", "Filtered Water Bottle", "Wide-Mouth Sport Bottle",
        "Infuser Fruit Water Bottle", "Electrolyte Hydration Sachets", "Sports Hydration Belt",
        "Bike Cage Water Bottle", "Camelbak Cleaning Kit", "Glass Water Bottle 1L",
        "Stainless Steel Straw Set", "Insulated Coffee Tumbler", "Gallon Water Bottle 128oz",
        "Alkaline Water Flask", "Kids Water Bottle Spill-Proof", "Copper Water Vessel",
        "Hydrogen Water Generator", "Portable Water Softener",
    ],
}

# Product descriptions
DESCRIPTIONS = [
    "Premium quality product designed for optimal performance and durability.",
    "Professional-grade equipment meeting industry standards for serious athletes.",
    "Engineered with advanced technology for maximum efficiency and results.",
    "Built to last with superior materials and expert craftsmanship.",
    "Ideal for beginners and advanced users alike with versatile features.",
    "Experience unmatched comfort and functionality with this innovative design.",
    "Trusted by athletes and fitness professionals worldwide for consistent quality.",
    "Features cutting-edge design combined with practical everyday usability.",
    "Delivers exceptional value with premium features at an affordable price point.",
    "Backed by rigorous testing and proven performance in real-world conditions.",
]

# Size options
SIZE_OPTIONS = [
    "XS,S,M,L,XL",
    "S,M,L,XL,XXL",
    "One Size",
    "6kg,8kg,12kg,16kg,20kg",
    "5kg,10kg,15kg,20kg",
    "Small,Medium,Large",
    "Standard",
    "32cm,38cm,45cm,52cm",
    "Youth,Adult,Large",
    "Light,Medium,Heavy",
]


def build_fixture() -> list:
    fixture = []
    random.seed(42)

    # Categories
    for pk, name in CATEGORIES:
        fixture.append({
            "model": "store.category",
            "pk": pk,
            "fields": {
                "name": name,
                "image": f"https://picsum.photos/seed/category-{pk}/800/600",
            },
        })

    # Products (20 per category)
    product_pk = 1001
    for cat_pk, cat_name in CATEGORIES:
        product_names = PRODUCT_NAMES[cat_pk]
        
        for i, product_name in enumerate(product_names):
            price = round(random.uniform(15, 150), 2)
            stock = random.randint(0, 100)
            rating = round(random.choice([0, 0, random.uniform(3.5, 5.0)]), 1)
            is_featured = random.random() < 0.2
            is_sale = random.random() < 0.15
            size = random.choice(SIZE_OPTIONS)
            description = random.choice(DESCRIPTIONS)
            
            fixture.append({
                "model": "store.product",
                "pk": product_pk,
                "fields": {
                    "name": f"{cat_name} – {product_name}",
                    "description": description,
                    "price": f"{price:.2f}",
                    "stock": stock,
                    "category": cat_pk,
                    "image": f"https://picsum.photos/seed/{product_pk}/600/400",
                    "is_featured": is_featured,
                    "is_sale": is_sale,
                    "rating": f"{rating:.1f}",
                    "size": size,
                },
            })
            product_pk += 1

    return fixture


def main():
    data = build_fixture()

    categories = [e for e in data if e["model"] == "store.category"]
    products = [e for e in data if e["model"] == "store.product"]
    
    assert len(categories) == 17, f"Expected 17 categories, got {len(categories)}"
    assert len(products) == 340, f"Expected 340 products, got {len(products)}"
    
    pks = [p["pk"] for p in products]
    assert pks[0] == 1001
    assert pks[-1] == 1340
    
    names = [p["fields"]["name"] for p in products]
    assert len(names) == len(set(names)), "Duplicate product names detected!"
    
    print("✅ Fixture validation passed!")
    print(f"   Categories: {len(categories)}")
    print(f"   Products:   {len(products)} (PKs {pks[0]}–{pks[-1]})")
    print("   Products per category: 20")

    output_path = "store_data.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Fixture written to '{output_path}'")
    print("\n📝 Load with:")
    print(f"   python manage.py loaddata {output_path}")


if __name__ == "__main__":
    main()