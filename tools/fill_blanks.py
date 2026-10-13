import openpyxl
import re

file_path = 'HRZ_Pitstop_Client_Inventory_All_Bike_Models.xlsx'
wb = openpyxl.load_workbook(file_path)

# Comprehensive bike mapping to extract Make and Model from product names
# Model string mapped to (Make, Standardized Model Name)
bike_signatures = {
    # ROYAL ENFIELD
    "scram 440": ("Royal Enfield", "Scram 440 new"),
    "scram 411": ("Royal Enfield", "Scram"),
    "scram": ("Royal Enfield", "Scram"),
    "classic 650": ("Royal Enfield", "Classic 650"),
    "bear 650": ("Royal Enfield", "Bear 650"),
    "guerrilla 450": ("Royal Enfield", "Guerrilla 450"),
    "guerrilla": ("Royal Enfield", "Guerrilla 450"),
    "himalayan 450": ("Royal Enfield", "Himalayan 450"),
    "himalayan 411": ("Royal Enfield", "Himalayan"),
    "himalayan": ("Royal Enfield", "Himalayan"),
    "super meteor": ("Royal Enfield", "SUPER METEOR 650"),
    "meteor 350": ("Royal Enfield", "Meteor 350"),
    "meteor": ("Royal Enfield", "Meteor 350"),
    "hunter 350": ("Royal Enfield", "Hunter 350"),
    "hunter": ("Royal Enfield", "Hunter 350"),
    "classic 350 reborn": ("Royal Enfield", "Classic 350 Reborn"),
    "classic reborn": ("Royal Enfield", "Classic 350 Reborn"),
    "reborn": ("Royal Enfield", "Classic 350 Reborn"),
    "standard 350 reborn": ("Royal Enfield", "Standard 350 Reborn"),
    "classic 350": ("Royal Enfield", "Classic"),
    "classic": ("Royal Enfield", "Classic"),
    "standard 350": ("Royal Enfield", "Standard"),
    "standard": ("Royal Enfield", "Standard"),
    "electra": ("Royal Enfield", "Electra"),
    "interceptor 650": ("Royal Enfield", "Interceptor"),
    "interceptor": ("Royal Enfield", "Interceptor"),
    "continental gt 650": ("Royal Enfield", "Continental GT"),
    "continental gt": ("Royal Enfield", "Continental GT"),
    "gt 650": ("Royal Enfield", "Continental GT"),
    "thunderbird x": ("Royal Enfield", "Thunderbird X"),
    "thunderbird": ("Royal Enfield", "Thunderbird"),
    "bullet": ("Royal Enfield", "Standard"),
    
    # KTM
    "adv 390": ("KTM", "Adventure 390"),
    "adventure 390": ("KTM", "Adventure 390"),
    "adv 250": ("KTM", "Adventure 250"),
    "adventure 250": ("KTM", "Adventure 250"),
    "390 adv": ("KTM", "Adventure 390"),
    "250 adv": ("KTM", "Adventure 250"),
    "duke 390": ("KTM", "Duke 390"),
    "duke 250": ("KTM", "Duke 250"),
    "duke 200": ("KTM", "Duke 200"),
    "duke 125": ("KTM", "Duke 125"),
    "rc 390": ("KTM", "RC 390"),
    "ktm adv": ("KTM", "Adventure 390"),
    
    # YAMAHA
    "xsr 155": ("Yamaha", "XSR 155"),
    "xsr155": ("Yamaha", "XSR 155"),
    "rx 100": ("Yamaha", "RX 100"),
    "rx100": ("Yamaha", "RX 100"),
    "aerox 155": ("Yamaha", "Aerox 155"),
    "aerox": ("Yamaha", "Aerox 155"),
    "mt 15": ("Yamaha", "MT 15"),
    "mt15": ("Yamaha", "MT 15"),
    "r15 v4": ("Yamaha", "R15 V4"),
    "r15 v3": ("Yamaha", "R15 V3"),
    "r15": ("Yamaha", "R15 V4"),
    "r3": ("Yamaha", "R3"),
    
    # BAJAJ
    "ns400z": ("Bajaj", "NS400Z"),
    "ns400": ("Bajaj", "NS400Z"),
    "pulsar 220": ("Bajaj", "Pulsar 220"),
    "ns 200": ("Bajaj", "Pulsar NS 200"),
    "ns200": ("Bajaj", "Pulsar NS 200"),
    "rs 200": ("Bajaj", "Pulsar RS 200"),
    "rs200": ("Bajaj", "Pulsar RS 200"),
    "dominar 400": ("Bajaj", "Dominar 400"),
    "dominar 250": ("Bajaj", "Dominar 250"),
    "dominar": ("Bajaj", "Dominar 400"),
    
    # HONDA
    "transalp 750": ("Honda", "XL750 Transalp"),
    "transalp": ("Honda", "XL750 Transalp"),
    "nx500": ("Honda", "NX500"),
    "cb 200x": ("Honda", "CB 200X"),
    "cb200x": ("Honda", "CB 200X"),
    "hness cb 350": ("Honda", "Hness CB 350"),
    "hness": ("Honda", "Hness CB 350"),
    "h'ness": ("Honda", "Hness CB 350"),
    "highness": ("Honda", "Hness CB 350"),
    "cb 350 rs": ("Honda", "CB 350 RS"),
    "cb350 rs": ("Honda", "CB 350 RS"),
    "cb350": ("Honda", "Hness CB 350"),
    "cb 500x": ("Honda", "CB 500X"),
    "cb500x": ("Honda", "CB 500X"),
    
    # SUZUKI
    "gixxer sf": ("Suzuki", "Gixxer SF"),
    "gixxer": ("Suzuki", "Gixxer"),
    "v strom 250": ("Suzuki", "V Strom 250"),
    "v strom 800de": ("Suzuki", "V Strom 800DE"),
    "v strom dl650": ("Suzuki", "V Strom DL650"),
    "v strom": ("Suzuki", "V Strom 250"),
    "v-strom": ("Suzuki", "V Strom 250"),
    "vstrom": ("Suzuki", "V Strom 250"),
    "hayabusa": ("Suzuki", "Hayabusa"),
    
    # HERO
    "xpulse 210": ("Hero", "Xpulse 210"),
    "xpulse 200": ("Hero", "Xpulse 200"),
    "xpulse": ("Hero", "Xpulse 200"),
    "mavrick 440": ("Hero", "Mavrick 440"),
    "mavrick": ("Hero", "Mavrick 440"),
    "karizma": ("Hero", "Karizma"),
    
    # TRIUMPH
    "tiger 900": ("Triumph", "Tiger 900"),
    "tiger sport 660": ("Triumph", "Tiger Sport 660"),
    "tiger 800": ("Triumph", "Tiger"),
    "tiger": ("Triumph", "Tiger"),
    "tracker 400": ("Triumph", "Tracker 400"),
    "scrambler 400 x": ("Triumph", "Scrambler 400 x"),
    "scrambler 400x": ("Triumph", "Scrambler 400 x"),
    "scrambler 400": ("Triumph", "Scrambler 400 x"),
    "speed 400": ("Triumph", "Speed 400"),
    "trident 660": ("Triumph", "Trident 660"),
    "trident": ("Triumph", "Trident 660"),
    
    # TVS
    "apache rtx 300": ("TVS", "Apache RTX 300 new"),
    "ronin": ("TVS", "tvs ronin"),
    "apache rtr 310": ("TVS", "Apache RTR 310"),
    "apache 310": ("TVS", "Apache RTR 310"),
    "rr310": ("TVS", "Apache RTR 310"),
    "rr 310": ("TVS", "Apache RTR 310"),
    "apache 200": ("TVS", "Apache 200"),
    
    # HARLEY
    "harley 440x": ("Harley Davidson", "Harley 440X"),
    "x440": ("Harley Davidson", "Harley 440X"),
    
    # BMW
    "g 310 gs": ("BMW", "G 310GS"),
    "310 gs": ("BMW", "G 310GS"),
    "310gs": ("BMW", "G 310GS"),
    "g 310 r": ("BMW", "G 310 R"),
    "310 r": ("BMW", "G 310 R"),
    "r 1250 gs": ("BMW", "R 1200GS"),
    "r 1300 gs": ("BMW", "R 1300GS"),
    
    # KAWASAKI
    "versys 650": ("Kawasaki", "Versys 650"),
    "versys": ("Kawasaki", "Versys 650"),
    "ninja 300": ("Kawasaki", "Ninja 300"),
    "ninja 400": ("Kawasaki", "Ninja 400"),
    "z900": ("Kawasaki", "Z900"),
    "zx-10r": ("Kawasaki", "Ninja ZX-10R")
}

def extract_bike(name):
    name_lower = name.lower()
    
    # Check explicitly defined models
    for sig, (make, model) in bike_signatures.items():
        # Match word boundaries to prevent "scram" matching "scrambler"
        if re.search(r'\b' + re.escape(sig) + r'\b', name_lower):
            return make, model
            
    # Check explicitly defined makes
    makes = ["Royal Enfield", "KTM", "Yamaha", "Bajaj", "Honda", "Suzuki", "Hero", "Triumph", "TVS", "Harley Davidson", "BMW", "Kawasaki"]
    for make in makes:
        if re.search(r'\b' + re.escape(make.lower()) + r'\b', name_lower):
            return make, "Universal"
            
    return None, None

main_sheets = wb.sheetnames[:14]
blanks_filled = 0

for s_name in main_sheets:
    sheet = wb[s_name]
    for row in range(2, sheet.max_row + 1):
        name = sheet.cell(row=row, column=1).value
        if not name:
            continue
            
        make = sheet.cell(row=row, column=4).value
        model = sheet.cell(row=row, column=5).value
        
        # If either is blank or 'Universal', try to extract from name
        if not make or not model or model == 'Universal':
            extracted_make, extracted_model = extract_bike(name)
            if extracted_make:
                # Only overwrite if it was blank or if we found a highly confident match
                if not make:
                    sheet.cell(row=row, column=4).value = extracted_make
                if not model or model == 'Universal':
                    sheet.cell(row=row, column=5).value = extracted_model
                blanks_filled += 1

wb.save(file_path)
print(f"Successfully scanned all names and filled in {blanks_filled} missing bike compatibilities.")
