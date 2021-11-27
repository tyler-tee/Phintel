# Phintel
<table>
<tr>
<td>
    Phintel is a Dash-based app built to automatically extract and transform multiple disparate phishing intelligence feeds into a single set of actionable data. Additional tools are included for extended visualization and analysis.
</td>
</tr>
</table>

# ![Phintel](https://user-images.githubusercontent.com/64701075/143721697-c192608d-7831-440b-81da-6e828c67dc75.JPG)


## Current Data Sources
- [Openphish](https://openphish.com/)
- [Phishstats](https://phishstats.info/)
- [Phishtank](https://phishtank.org/)
- [URLhaus](https://urlhaus.abuse.ch/)

## Current Features

### Visualizations
![Charts](https://user-images.githubusercontent.com/64701075/143721700-f9f6cfa2-a927-42c0-b643-b94da4a4d815.jpg)

### Live Dataset Exploration
![Dataset](https://user-images.githubusercontent.com/64701075/143721698-669037ac-59f7-4a2c-a65e-7c90115a5aec.jpg)

### ML-Based Analysis
![ML](https://user-images.githubusercontent.com/64701075/143721699-e6b563d0-0dc7-485e-9218-b70e6bb9a87a.jpg)


## Usage

### Docker (Recommended)
```
docker build -f ./DockerFile . -t 'phintel:0.1.0'
docker run -p 8050:8050 phintel
```

### Setup (Manual)
```
python3 -m pip install requirements.txt
```
- Register at [Phishtank](https://phishtank.org/register.php) to generate an API key for Phishtank's data feed. This key will need to be included in config.py as a variable for import.

### Running Phintel
```
python ./main.py
```
The app will be accessible locally on port 8050.

### Development
Contribution welcome.

To fix a bug or enhance an existing module, follow these steps:

- Fork the repo
- Create a new branch (`git checkout -b improve-feature`)
- Make the appropriate changes in the files
- Add changes to reflect the changes made
- Commit your changes (`git commit -am 'Improve feature'`)
- Push to the branch (`git push origin improve-feature`)
- Create a Pull Request 

## Built with 

- [Dash](https://dash.plotly.com/introduction) - Dash is the original low-code framework for rapidly building data apps in Python, R, Julia, F#, and MATLAB®.

## To-do
- [X] Build and test Docker image for portability.
- [X] Add 'About' page.
- [ ] Add 'OSINT' page.

## License

[MIT](https://choosealicense.com/licenses/mit/)