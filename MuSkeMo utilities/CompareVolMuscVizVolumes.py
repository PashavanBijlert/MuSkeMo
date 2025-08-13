### Run this script in the script editor, after loading in a MuSkeMo model and turning on the volumetric muscle visualizations.
### It assumes your muscles either end with '_r' (for right side) or '_l' (for left side), you can modify this.
### For all muscles, it sets the TendonMuscleRadiusRatio to 0, effectively turning off the tendons.
### It computes the volumes of the right side using the "Fast" mode, and the left side using the "VolumeAccurate" mode.
### The volumes are compared with the Hill muscle volume encoded in the muscle itself, the output is printed to the System Console (Window > Toggle System Console),
### and also printed out as a CSV file. 
### The script works for Emu model in the sample dataset, and may require minor modifications if your muscles have different side strings.
### For the emu model, in the base posture, the Fast mode underestimates actual volume by 0 - 3.6%, with an average of 2.5% underestimation.
### This discrepancy will be dependent on posture and muscle visualization settings, and the discrepancy can be more extreme with certain combinations (e.g. 8% difference).
### The VolumeAccurate is approximately twice as slow.

### Author: Pasha van Bijlert
### Date: 13/8/2025


import bpy
import bmesh
import csv
import os



def compute_volume(obj):
    """Compute volume of evaluated mesh in object space."""
    depsgraph = bpy.context.evaluated_depsgraph_get()
    eval_obj = obj.evaluated_get(depsgraph)
    mesh = eval_obj.to_mesh()

    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    vol = bm.calc_volume(signed=False)

    bm.free()
    eval_obj.to_mesh_clear()
    return vol

right_side_string = '_r'
left_side_string = '_l'


#Get all the right sided and left sided muscles in separate dicts
right_sided_muscles = [x for x in bpy.data.objects if x.get("MuSkeMo_type") == 'MUSCLE' and right_side_string in x.name]
left_sided_muscles  = [x for x in bpy.data.objects if x.get("MuSkeMo_type") == 'MUSCLE' and left_side_string in x.name]

fast_results = []
accurate_results = []

#loop through right sided muscles
for m in right_sided_muscles:
    geonode = m.modifiers.get(m.name + '_VolumetricMuscleViz')
    if geonode is None or geonode.type != 'NODES':
        continue
    
    geonode["Socket_1"] = 0  # set tendon muscle radius ratio to 0
    vol_encoded = geonode["Socket_2"] #get the hill type muscle volume

    vol_actual = compute_volume(m) #compute the mesh muscle volume
    perc_off = ((vol_actual - vol_encoded) / vol_actual) * 100 if vol_actual != 0 else 0
    fast_results.append((m.name, 'Fast', vol_encoded, vol_actual, perc_off))


for m in left_sided_muscles:
    geonode = m.modifiers.get(m.name + '_VolumetricMuscleViz')
    if geonode is None or geonode.type != 'NODES':
        continue
    
    geonode["Socket_1"] = 0  # tendon muscle radius ratio to 0
    geonode["Socket_4"] = 1  # assuming 'VolumeAccurate' corresponds to enum index 1
    vol_encoded = geonode["Socket_2"]

    vol_actual = compute_volume(m)
    perc_off = ((vol_actual - vol_encoded) / vol_actual) * 100 if vol_actual != 0 else 0
    accurate_results.append((m.name, 'VolumeAccurate', vol_encoded, vol_actual, perc_off))


# Print results for Fast mode
print("\n=== Fast Mode (Right Sided) ===")
print(f"{'Muscle':30} | {'Mode':^14} | {'Encoded':>12} | {'Actual':>12} | {'% Off':>10}")
print("-"*90)
for name, mode, enc, act, perc in fast_results:
    print(f"{name:30} | {mode:^14} | {enc:12.6f} | {act:12.6f} | {perc:10.2f}")

# Average percentage difference for Fast mode
if fast_results:
    avg_fast = sum(r[4] for r in fast_results) / len(fast_results)
    print(f"\nAverage % Off (Fast mode): {avg_fast:.2f}%")
else:
    avg_fast = None

# Print results for VolumeAccurate mode
print("\n=== VolumeAccurate Mode (Left Sided) ===")
print(f"{'Muscle':30} | {'Mode':^14} | {'Encoded':>12} | {'Actual':>12} | {'% Off':>10}")
print("-"*90)
for name, mode, enc, act, perc in accurate_results:
    print(f"{name:30} | {mode:^14} | {enc:12.6f} | {act:12.6f} | {perc:10.2f}")


# Write to CSV
csv_path = os.path.join(bpy.path.abspath("//"), "muscle_volume_comparison.csv")
with open(csv_path, mode="w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["Muscle", "Mode", "Encoded Volume", "Actual Volume", "% Off"])
    for row in fast_results + accurate_results:
        writer.writerow(row)

print(f"\nCSV written to: {csv_path}")
