
# Script for running all comparisons in a simulation set
# Note that cross-comparisons between faces are not included.

for j in {0..4} # Loop through Fiducials
do
    for face in {0..2} # Loop through faces
    do
        python output.py Fiducial${j}.${face}.0 $face fiducial${j}.${face} F
        cd /srv/astro/erickoch/Dropbox/code_development/TurbuStat/Examples
    done
done

## Fiducial Comparisons
for face in {0..2}
do
    python output.py fid_comp $face fiducial_comparisons_face${face} F 10 F
    cd /srv/astro/erickoch/Dropbox/code_development/TurbuStat/Examples
done