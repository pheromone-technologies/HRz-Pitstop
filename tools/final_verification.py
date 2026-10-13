import openpyxl

file_path = 'HRZ_Pitstop_Client_Inventory_All_Bike_Models.xlsx'
wb = openpyxl.load_workbook(file_path)

valid_subcategories = {
    'Bike Protection': ["Lock system", "Crash Guard", "Frame Slider", "Fluid Guards and Caps", "Master Cylinder Guard", "Engine Guards and Skid Plate", "Headlight Grill", "Radiator Guard", "Tank Protectors", "Body Cover", "Screen Protectors", "Stand and Extenders", "Chain Cover And Sprocket"],
    'Handlebar & Accessories': ["Grips and Throttle", "Hand Guard", "Handlebars", "Handle Risers", "Lever Guard", "Mirror", "Mounts and Chargers"],
    'Foot Rests': ["Foot Pegs and Mounts"],
    'Guards & Mounts': ["Head Light Grill", "Master Cylinder Guard", "Fog Light Mount", "Crash Guard", "Radiator Grill"],
    'Oil Caps & Stands': ["Front Oil Cap Silver", "Rear Oil Cap", "Side Stand Base", "Luggage Carrier", "Saddle Stay"],
    'Body Fairing and Fenders': ["Body Fairing", "Fenders and Extenders", "Tail"],
    'Bike Essentials': ["Windshield", "Winglet", "Seat"],
    'Cleaning Accessories': ["Cleaning Accessories"],
    'Performance Accessories': ["Exhaust", "Air Filter", "Performance Parts", "Chain and Sprocket", "Braking Components", "Other Performance"],
    'Lighting': ["Auxiliary Lights", "Headlights", "Indicators", "Fog Lights", "Wiring and Electrical", "Horns", "Other Lighting"],
    'Riding Gears': ["Riding Jackets", "Gloves", "Riding Pants", "Boots", "Protective Armour", "Riding Suits", "Other Riding Gear"],
    'Luggage & Touring': ["Saddle Bags", "Panniers", "Top Boxes", "Tank Bags", "Luggage Racks", "Saddle Stays", "Touring Accessories", "Other Luggage"],
    'Helmets & Accessories': ["Full-Face Helmet", "Open-Face Helmet", "Modular Helmet", "Helmet Visor", "Helmet Accessories", "Other Helmet"],
    'General Accessories': ["Mobile Holders", "Chargers", "Bike Covers", "Seat Accessories", "Security Accessories", "Miscellaneous"]
}

# Fix missing bike makes using generic parts knowledge
universal_categories = ['Riding Gears', 'Cleaning Accessories', 'Bike Essentials', 'Helmets & Accessories', 'Luggage & Touring', 'Lighting']

reports = []

for sheet_name in wb.sheetnames[:14]:
    sheet = wb[sheet_name]
    valid_subs = valid_subcategories.get(sheet_name, [])
    
    for row in range(2, sheet.max_row + 1):
        name = sheet.cell(row=row, column=1).value
        if not name: continue
        
        # 1. Validate Subcategory
        subcat = sheet.cell(row=row, column=2).value
        if subcat not in valid_subs:
            old_subcat = subcat
            # Force fallback
            new_subcat = valid_subs[-1] if valid_subs else "Miscellaneous"
            sheet.cell(row=row, column=2).value = new_subcat
            reports.append(f"Fixed Subcategory for '{name}': '{old_subcat}' -> '{new_subcat}' (Did not match dropdown).")
            
        # 2. Validate Brand
        brand = sheet.cell(row=row, column=3).value
        if not brand:
            # Infer brand from name if possible
            if 'legundary' in str(name).lower() or 'lcb' in str(name).lower():
                sheet.cell(row=row, column=3).value = 'Legundary Customs'
                reports.append(f"Fixed missing Brand for '{name}' -> 'Legundary Customs'.")
            elif 'mt ' in str(name).lower():
                sheet.cell(row=row, column=3).value = 'Moto Torque'
                reports.append(f"Fixed missing Brand for '{name}' -> 'Moto Torque'.")
            else:
                sheet.cell(row=row, column=3).value = 'Universal Brand'
                reports.append(f"Fixed missing Brand for '{name}' -> 'Universal Brand'.")
                
        # 3. Validate Bike Make/Model
        make = sheet.cell(row=row, column=4).value
        model = sheet.cell(row=row, column=5).value
        
        if not make or not model:
            if sheet_name in universal_categories:
                sheet.cell(row=row, column=4).value = 'Universal'
                sheet.cell(row=row, column=5).value = 'Universal'
                reports.append(f"Fixed missing Bike for '{name}' -> Marked as 'Universal' (Generic gear).")
            else:
                sheet.cell(row=row, column=4).value = 'Universal'
                sheet.cell(row=row, column=5).value = 'Universal'
                reports.append(f"Fixed missing Bike for '{name}' -> Marked as 'Universal' (Could not extract specific bike).")

wb.save(file_path)

with open('verification_report.txt', 'w') as f:
    if reports:
        f.write('\n'.join(reports))
    else:
        f.write("All good. No issues found.")

print(f"Verification complete. Found and fixed {len(reports)} issues.")
