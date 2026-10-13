import openpyxl
import re

file_path = 'HRZ_Pitstop_Client_Inventory_All_Bike_Models.xlsx'
wb = openpyxl.load_workbook(file_path)

bike_signatures = {
    # ROYAL ENFIELD
    "scram440": ("Royal Enfield", "Scram 440 new"),
    "scram411": ("Royal Enfield", "Scram"),
    "classic650": ("Royal Enfield", "Classic 650"),
    "bear650": ("Royal Enfield", "Bear 650"),
    "guerrilla450": ("Royal Enfield", "Guerrilla 450"),
    "guerrilla": ("Royal Enfield", "Guerrilla 450"),
    "himalayan450": ("Royal Enfield", "Himalayan 450"),
    "himalayan411": ("Royal Enfield", "Himalayan"),
    "supermeteor": ("Royal Enfield", "SUPER METEOR 650"),
    "meteor350": ("Royal Enfield", "Meteor 350"),
    "hunter350": ("Royal Enfield", "Hunter 350"),
    "classic350reborn": ("Royal Enfield", "Classic 350 Reborn"),
    "standard350reborn": ("Royal Enfield", "Standard 350 Reborn"),
    "classic350": ("Royal Enfield", "Classic"),
    "standard350": ("Royal Enfield", "Standard"),
    "electra": ("Royal Enfield", "Electra"),
    "interceptor650": ("Royal Enfield", "Interceptor"),
    "interceptor": ("Royal Enfield", "Interceptor"),
    "continentalgt": ("Royal Enfield", "Continental GT"),
    "gt650": ("Royal Enfield", "Continental GT"),
    "thunderbirdx": ("Royal Enfield", "Thunderbird X"),
    "thunderbird": ("Royal Enfield", "Thunderbird"),
    "himalayan": ("Royal Enfield", "Himalayan"),
    
    # KTM
    "adv390": ("KTM", "Adventure 390"),
    "adventure390": ("KTM", "Adventure 390"),
    "adv250": ("KTM", "Adventure 250"),
    "adventure250": ("KTM", "Adventure 250"),
    "390enduror": ("KTM", "390 Enduro R"),
    "enduror": ("KTM", "390 Enduro R"),
    "duke390": ("KTM", "Duke 390"),
    "duke250": ("KTM", "Duke 250"),
    "duke200": ("KTM", "Duke 200"),
    "duke125": ("KTM", "Duke 125"),
    "rc390": ("KTM", "RC 390"),
    
    # YAMAHA
    "xsr155": ("Yamaha", "XSR 155"),
    "rx100": ("Yamaha", "RX 100"),
    "aerox155": ("Yamaha", "Aerox 155"),
    "mt15": ("Yamaha", "MT 15"),
    "r15v4": ("Yamaha", "R15 V4"),
    "r15v3": ("Yamaha", "R15 V3"),
    "r3": ("Yamaha", "R3"),
    "fzsv3": ("Yamaha", "FZS V3"),
    "fzsv4": ("Yamaha", "FZS V4"),
    
    # BAJAJ
    "ns400z": ("Bajaj", "NS400Z"),
    "ns400": ("Bajaj", "NS400Z"),
    "pulsar220": ("Bajaj", "Pulsar 220"),
    "ns200": ("Bajaj", "Pulsar NS 200"),
    "rs200": ("Bajaj", "Pulsar RS 200"),
    "dominar400": ("Bajaj", "Dominar 400"),
    "dominar250": ("Bajaj", "Dominar 250"),
    
    # HONDA
    "transalp750": ("Honda", "XL750 Transalp"),
    "transalp": ("Honda", "XL750 Transalp"),
    "nx500": ("Honda", "NX500"),
    "cb200x": ("Honda", "CB 200X"),
    "hnesscb350": ("Honda", "Hness CB 350"),
    "hness": ("Honda", "Hness CB 350"),
    "cb350rs": ("Honda", "CB 350 RS"),
    "cb350": ("Honda", "Hness CB 350"),
    "cb500x": ("Honda", "CB 500X"),
    
    # SUZUKI
    "gixxersf": ("Suzuki", "Gixxer SF"),
    "vstrom250": ("Suzuki", "V Strom 250"),
    "vstorm250": ("Suzuki", "V Strom 250"),
    "vstrom800de": ("Suzuki", "V Strom 800DE"),
    "vstromdl650": ("Suzuki", "V Strom DL650"),
    "vstrom": ("Suzuki", "V Strom 250"),
    "vstorm": ("Suzuki", "V Strom 250"),
    "hayabusa": ("Suzuki", "Hayabusa"),
    
    # HERO
    "xpulse210": ("Hero", "Xpulse 210"),
    "xpulse200": ("Hero", "Xpulse 200"),
    "xpulse": ("Hero", "Xpulse 200"),
    "mavrick440": ("Hero", "Mavrick 440"),
    "karizma": ("Hero", "Karizma"),
    
    # TRIUMPH
    "tiger900": ("Triumph", "Tiger 900"),
    "tigersport660": ("Triumph", "Tiger Sport 660"),
    "tracker400": ("Triumph", "Tracker 400"),
    "scrambler400x": ("Triumph", "Scrambler 400 x"),
    "scrambler400": ("Triumph", "Scrambler 400 x"),
    "speed400": ("Triumph", "Speed 400"),
    "trident660": ("Triumph", "Trident 660"),
    "triumph": ("Triumph", "Universal"), # If just Triumph is mentioned
    
    # TVS
    "apachertx300": ("TVS", "Apache RTX 300 new"),
    "ronin": ("TVS", "tvs ronin"),
    "apachertr310": ("TVS", "Apache RTR 310"),
    "rtr310": ("TVS", "Apache RTR 310"),
    "rr310": ("TVS", "Apache RTR 310"),
    "apache200": ("TVS", "Apache 200"),
    
    # HARLEY
    "harley440x": ("Harley Davidson", "Harley 440X"),
    "davidson440x": ("Harley Davidson", "Harley 440X"),
    "x440": ("Harley Davidson", "Harley 440X"),
    
    # BMW
    "g310gs": ("BMW", "G 310GS"),
    "310gs": ("BMW", "G 310GS"),
    "g310r": ("BMW", "G 310 R"),
    "310r": ("BMW", "G 310 R"),
    "r1250gs": ("BMW", "R 1200GS"),
    "r1300gs": ("BMW", "R 1300GS"),
    "f450gs": ("BMW", "F 450 GS"),
    
    # KAWASAKI
    "versys650": ("Kawasaki", "Versys 650"),
    "ninja300": ("Kawasaki", "Ninja 300"),
    "ninja400": ("Kawasaki", "Ninja 400"),
    "z900": ("Kawasaki", "Z900"),
    "zx10r": ("Kawasaki", "Ninja ZX-10R"),
    "klx230": ("Kawasaki", "KLX 230")
}

makes = ["royalenfield", "ktm", "yamaha", "bajaj", "honda", "suzuki", "hero", "triumph", "tvs", "harleydavidson", "bmw", "kawasaki"]

def extract_bike(name):
    name_clean = re.sub(r'[^a-z0-9]', '', name.lower())
    
    # Sort signatures by length descending so longer matches happen first (e.g., scrambler400x before scrambler400)
    sorted_sigs = sorted(bike_signatures.items(), key=lambda x: len(x[0]), reverse=True)
    
    for sig, (make, model) in sorted_sigs:
        if sig in name_clean:
            return make, model
            
    for make in makes:
        if make in name_clean:
            # Re-map original formatting
            formatted_make = "Royal Enfield" if make == "royalenfield" else "Harley Davidson" if make == "harleydavidson" else make.capitalize()
            if make == "bmw": formatted_make = "BMW"
            if make == "ktm": formatted_make = "KTM"
            if make == "tvs": formatted_make = "TVS"
            return formatted_make, "Universal"
            
    return None, None

main_sheets = wb.sheetnames[:14]
blanks_filled = 0

for s_name in main_sheets:
    sheet = wb[s_name]
    for row in range(2, sheet.max_row + 1):
        name = sheet.cell(row=row, column=1).value
        if not name: continue
            
        make = sheet.cell(row=row, column=4).value
        model = sheet.cell(row=row, column=5).value
        
        if not make or not model or model == 'Universal':
            extracted_make, extracted_model = extract_bike(name)
            if extracted_make:
                if not make:
                    sheet.cell(row=row, column=4).value = extracted_make
                if not model or model == 'Universal':
                    sheet.cell(row=row, column=5).value = extracted_model
                blanks_filled += 1

wb.save(file_path)
print(f"Aggressive pass successfully scanned and filled {blanks_filled} tricky missing bike compatibilities.")
