# Isearch (OSINT) 🔎

Face recognition reverse image search on Instagram profile feed photos. 

<img src="https://github.com/maleksal/isearch-osint/blob/main/carbon.png" alt="carbon(1)" style="zoom:100%;" />

Disclaimer: **FOR EDUCATIONAL PURPOSE ONLY! **

> You might encounter (false positive / false negative) results. This because Face recognition uses hog as a model which is fast but low on accuracy, the other model can be 'cnn' which is high on accuracy but very slow (on CPU && fast on GPU)



## Installation

**Dlib installation**: (full guide: https://www.pyimagesearch.com/2017/03/27/how-to-install-dlib/)

```bash
# Install prerequisites
$ sudo apt-get install build-essential cmake
$ sudo apt-get install libgtk-3-dev
$ sudo apt-get install libboost-all-dev
```

**Note:** dlib installation will take few minutes

```bash
# Install dlib python
$ python3 -m pip install dlib
```

```bash
# Other requirements
$ python3 -m pip install -r requirements.txt
```



## Usage

Set your Instagram username, password in config/credentials.ini, Also you might want to consider using a burner account.

```bash
# Face search in all target feed photos 
$ python3 isearch-cli <path-to-face-images-folder> <instagram_profile_username>

# Face search only 5 photos from target feed 
$ python3 isearch-cli <path-to-face-images-folder> <instagram_profile_username> --limit 5
```

**Options:**

```
  --limit INTEGER  Number of photos to Download and process from target_profile
```
