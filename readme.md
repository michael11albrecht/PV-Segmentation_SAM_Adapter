# Important:
when using cpu/cuda for training, line 98 in sam.py has to be changed between 'cpu' and 'cuda'

# Short:
Requirements:
- ```console
    pip install -r requirements.txt
    mim install mmcv
    ```
- install [pytorch](https://pytorch.org/get-started/locally)

Preprocessing:
- Needed data:
- Folder with all *.geotif tiles of the respected area
- Folder with all *.geojson files containing polygons as masks, masking pv-panels in the area
- to Run:
    - ```console
        python run.py --runtype all --geotif path/to/geotiffolder/ --geojson path/to/geojsonfolder/ --splitsize 512
        ```
    - ```console
        python run.py --runtype split --geojson path/to/geojsonfolder --splitimages path/to/imagesfolder/ --splitmasks path/to/masksfolder/ --splitsize 512
        ```

Training:
- CPU/Cuda:
    - CPU: train_min_ma_checkpoint.py
    - Cuda: train_cuda.py
    - **! sam.py line 98 needs to be adjusted !**

- Needed data:
    - pretrained sam-weights
    - preprocessed test/eval images/masks (-->Preprocessing)
        - config File
- to Run:
    - ```console
        python train_min_ma_checkpoint.py --config configs/ma_B.yaml
        ```
    - ```console
        python -m torch.distributed.launch train_cuda.py --config configs/ma_B_cuda.yaml
        ```

Testing:
- Needed data:
    - trained weights (--> Training)
    - test images/masks
    - config File (equal to Training)
- to Run:
    - CPU: 
        ```console
        python test_min.py --config configs/ma_B.yaml --model save/... 
        ```
    - GPU:
        ```console
        python test_cuda.py --config configs/ma_B_cuda.yaml --model save/... 
        ```
Postprocessing:
- Needed data:
    - predicted masks (--> Testing)
- to Run:
    - ma_show_results.py (Build overlay showing true/false positive, true/false negative + iou)
    - ma_show_loss.py (shows loss during training based on logs)
    - ma_make_overlay.py (Build img/mask overlay)
    - ma_make_hist.py (Build mask histogram)
    - ma_make_binary_50.py (Build Binary-Mask with 50% threshold)
    - ma_make_contrast.py (0-1 Pixelvalue Image --> 0-255 Pixelvalue Grayscale Image)

Forwardpass:
- Needed data:
    - trained weights (--> Training)
    - config File (equal to Training)
- to Run:
    ```console
    python forwardpass/run_forwardpass.py --lat_1 --lon_1 --lat_2 --lon_2 --config --model
    ```

# Detailed:
Preprocessing:
- masks.py: small changes to the code of Yasmin mainly taken from [fixMatchSeg-Muc](https://github.com/yasminhossam/fixMatchSeg-Muc/blob/main/solarnet/preprocessing/masks.py) plus added bounding box creation (not used)
- load_munich.py: processing the geotif and geojson files to get the needed data for the dicts Jasmin uses in her code to calculate the masks
        - readTifKoos(): reading the UTM-coordinates of the geotif (Tiles)
        - readGeoJsonPoly(): reading the mask (Polygon) coordinates
        - buildReadData(): finding the tiles which include the masks, returning the dict mask.py creates the np-masks from
        - copyTif(): copys the tifs which include a mask to a seperate Folder
- split_ma.py: calculates the split and splits images/masks the same way.
    - calcSplit(): calculates the pixel-coordinates where the masks/images have to be cutted to get the needed image size. The function should return coordinates which create some overlapping if *mod(input-size/dest.-size) != 0*. If there is more overlapping needed (e.g. creating more trainings data) there can be added artificial overlapping (0-99%) using the input parameter. The algorithm is pretty basic and there is no proof for "the best" split.
- np2png_ma.py: converting np-masks to png-binary images.
- rename_union_new_ma.py: includes a info in the mask/image name to unite them into one trainings-set.
- proof_not_empty.py: checks if there is no (or below a absolute threshold (20)) mask (binary ones) in a mask and if so delets image + mask
- train_test_split_ma.py: splits the masks/images randomly in test/train/eval folders.

Training:
- CPU: train_min_ma_checkpoint.py: A training-loop only using the CPU and "normal" Memory. It's build to be run on systems which can't provide enough VRAM. Due to limited ressources the loop works by storing a checkpoint after each epoch and than continues by restarting the training from the last checkpoint. This enables you as well to restart the training from every checkpoint which makes the training flexible and resistent to failture.

- GPU: train_cuda.py: The unchanged training used in [SAM-Adapter-PyTorch](https://github.com/tianrun-chen/SAM-Adapter-PyTorch/tree/62a83a48b254fdd0cfb71e8be8df87dfa0d5a9d8) which works perfectly fine with enough VRAM.

Testing:
- CPU: test_min.py: A test-script just using the CPU and RAM to test. Also it saves the predictions as the GPU version does.
- GPU: test_cuda.py: A little updated version of the testing used in [SAM-Adapter-PyTorch](https://github.com/tianrun-chen/SAM-Adapter-PyTorch/tree/62a83a48b254fdd0cfb71e8be8df87dfa0d5a9d8). This test-script needs less VRAM by using tensors with disabled gradient calculation which makes it runable on just 8GB of VRAM and also saves the predicted segmentation masks during testing.

Postprocessing:
- ma_show results.py: Creates an overlay based on the predicted and ground truth mask showing the true positive, false positive and false negative parts of the mask. Also Calculates and adds the IoU per tile.
- ma_show_loss.py Creates a diagram showing the loss over the trained epochs. This is based on the log, which is written during training.
- ma_make_overlay.py: Creates a simple overlay overlaying the input image with the predicted mask.
- ma_make_hist.py: Simply creates a histogram of the given image. It was used during anlaysis of the predicted masks.
- ma_make_binary.py Just creates a binary image based on the masks which are build on values between 0 and 1.

Forwardpass:
- run_forwardpass.py: This script basicly runs a "pipeline" of all the steps needed to segment the PV-Systems in a sertain area in Bavaria by just passing the area in form of the WGS84 coordinates (lat,lon) and a already trained model. The pipeline contains of the following steps:
    - download the needed aerial imagery from the [open-data hub of bavaria](https://geodaten.bayern.de/opengeodata/OpenDataDetail.html?pn=dop40)
    - split the images into smaller tiles using the preprocessing function (also using the geo-information (coordinates of the small tiles in this case))
    - checking the coverd area for their land usage (get_land_useage_gpkg)
    - running the fw_cuda.py (which is basicly the test_cuda.py without the in fw-pass unnecessary metric calculation)
    - creating overlayed tiles
    - saving the masks as geotif with their georeference to use them e.g. in QGIS
- download_open_data.py: calculates the needed aerial images to cover the desired area and downloads the needed tiles from the [open-data hub of bavaria](https://geodaten.bayern.de/opengeodata/OpenDataDetail.html?pn=dop40). Internal calculation of the whole project runs in UTM 32T coordinates.
- get_land_usage_gpkg.py: The idea behind this script is to speed up the forwardpass by minimizing the amount of predictions. By use of the land usage map we can shrink down the search area, searching only at the areas where PV can be located.
    - downloads the [ALKIS land usage](https://geodaten.bayern.de/opengeodata/OpenDataDetail.html?pn=tatsaechlichenutzung) data from the bavarian open data hub as a geopackage (5GB).
    - Builds a search tree for both districts and different areas of land use in the district. Those are created and saved once first needed to speed up long calculation times.
    - The land use gets compared to a hardcoded list of important usages which can contain PV.
    - during a check operation there the district search tree and max. 4 already used inner district search trees will be held in memory to excellerate compute time but also make sure to not fill up the memory.
- save_geo.py: Takes the predicted mask and the georeference of the input image to create a georeferenced mask as geotif. This mask can than be importet into a GIS software for further analysis.

# Results:
- after 20 epochs training: [Dropbox](https://www.dropbox.com/scl/fo/fkaq4v9izj69md45fa6b6/h?rlkey=c5nn96kb3h8aoy7appsg55xde&dl=0) 
(DOP: Bayerische Vermessungsverwaltung – [www.geodaten.bayern.de](https://geodaten.bayern.de/opengeodata/OpenDataDetail.html?pn=dop40) (Daten verändert), Lizenz: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.de))
    - mean IoU over 88 test-images: 0.47234
- after 30 epochs training: [Dropbox](https://www.dropbox.com/scl/fo/ffs96v2vlc4ag1qlta19r/h?rlkey=ns63p2ae7fdjt8dfs84aduaez&dl=0)
(DOP: Bayerische Vermessungsverwaltung – [www.geodaten.bayern.de](https://geodaten.bayern.de/opengeodata/OpenDataDetail.html?pn=dop40) (Daten verändert), Lizenz: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.de)) 
    - mean IoU over 88 test-images: 0.47306
- Trained weights after 30 epochs: [Download](https://www.dropbox.com/scl/fo/38ltgx256k4pehvc4u5wq/h?rlkey=luip8tn2lm2mrgve5uk3zhfff&dl=0)

- Forwardpass using the 30 epochs Weights ![visualisation](https://github.com/michael11albrecht/PV-Segmentation_SAM_Adapter/blob/main/readme/ALKIS.PNG?raw=true)

# Information:
- pyTorch-SAM-adapter based on [Sam-Adapter-Pytorch](https://github.com/tianrun-chen/SAM-Adapter-PyTorch)
- supported by [Fortiss](https://fortiss.org)