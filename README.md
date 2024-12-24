# **Ambario**

<p align="center">
  <img src="https://upload.wikimedia.org/wikipedia/commons/c/c3/Python-logo-notext.svg" alt="Python Logo" width="100" />
  <img src="https://upload.wikimedia.org/wikipedia/commons/3/38/Jupyter_logo.svg" alt="Jupyter Lab Logo" width="100" />
  <img src="https://upload.wikimedia.org/wikipedia/commons/9/9a/Visual_Studio_Code_1.35_icon.svg" alt="VS Code Logo" width="100" />
</p>

---

## **Anggota Kelompok**

| **Nama**             | **NIM**   | **ID GITHUB**                                                                               |
| -------------------- | --------- | ------------------------------------------------------------------------------------------- |
| Arsyadana Estu Aziz  | 121140068 | <a href="https://github.com/Archiseino">@Archiseino</a>                                     |
| Fatur Arkan Syawalva | 121140229 | <a href="https://github.com/faturarkansyawalva_121140229">@faturarkansyawalva_121140229</a> |
| Alfath Elnandra      | 121140157 | <a href="https://github.com/Mas.El">@Mas.El</a>                                             |

---

## **Deskripsi Proyek**

Proyek ini mengembangkan permainan interaktif menggunakan Pygame yang dikendalikan melalui
input visual dari webcam dan input suara dari mikrofon secara real-time. Sistem memproses citra visual
menggunakan OpenCV (cv2) untuk mendeteksi gerakan atau isyarat, sementara tingkat kekerasan suara
(desibel) dari mikrofon digunakan sebagai parameter untuk mengontrol aksi karakter dalam permainan,
seperti melompat atau bergerak, menciptakan pengalaman bermain yang lebih dinamis dan responsif

---

## **Teknologi yang Digunakan**

Berikut adalah teknologi dan alat yang digunakan dalam proyek ini:

| Logo                                                                                                                           | Nama Teknologi | Fungsi                                                                           |
| ------------------------------------------------------------------------------------------------------------------------------ | -------------- | -------------------------------------------------------------------------------- |
| <img src="https://upload.wikimedia.org/wikipedia/commons/c/c3/Python-logo-notext.svg" alt="Python Logo" width="60">            | Python         | Bahasa pemrograman utama untuk pengembangan filter.                              |
| <img src="https://upload.wikimedia.org/wikipedia/commons/3/38/Jupyter_logo.svg" alt="Jupyter Lab Logo" width="60">             | Jupyter Lab    | Lingkungan pengembangan untuk menjalankan dan menguji skrip Python.              |
| <img src="https://upload.wikimedia.org/wikipedia/commons/9/9a/Visual_Studio_Code_1.35_icon.svg" alt="VS Code Logo" width="60"> | VS Code        | Editor teks untuk mengedit skrip secara efisien dengan dukungan ekstensi Python. |

---

## **Library yang Digunakan**

Berikut adalah daftar library Python yang digunakan dalam proyek ini, beserta fungsinya:

| **Library** | **Fungsi**                                                                                         |
| ----------- | -------------------------------------------------------------------------------------------------- |
| `cv2`       | Digunakan untuk menangkap gambar dari kamera dan memproses gambar secara langsung.                 |
| `mediapipe` | Digunakan untuk mendeteksi landmark wajah, seperti posisi hidung, untuk mendeteksi gerakan kepala. |
| `pyaudio`   | Digunakan untuk tempat masuk volume untuk proses deteksi suara..                                   |
| `wave`      | Digunakan untuk menyimpan audio dari mikrofon.                                                     |
| `threading` | Digunakan untuk melakukan threading input audio dan video ketika bermain.                          |
| `moviepy`   | Digunakan untuk menggabungkan file audio dan video secara sinkron.                                 |

---

## **Fitur**

### **1. Deteksi Teriakan**

- Filter ini bekerja dengan cara user berteriak dan dari terikan tersebut akan ditentukan berapa tinggi lompatan yang akan dilakukan.

---

## **How to Run**

Dengan asumsi bahwa sudah mempunyai environment manager seperti conda. maka buat environment baru seperti ini. Clone / fork lalu jalankan perintah ini.

```yaml
conda env create -f environment.yml
```

Lalu buka environemt yang sudah dibuat sebelumnya dengan, dan jalakan program main

```yaml
conda activate ambario
python Ambario.py
```
