# ![Phintel](https://user-images.githubusercontent.com/64701075/142785173-9bb257dc-9658-464b-87fd-f7b4e1af541c.jpg)
# Phintel
<table>
<tr>
<td>
    Phintel is a Dash-based app built to automatically extract and transform multiple disparate phishing intelligence feeds into a single set of actionable data. Additional tools are included for extended visualization and analysis.
</td>
</tr>
</table>

## Current Data Sources
- [Openphish](https://openphish.com/)
- [Phishstats](https://phishstats.info/)
- [Phishtank](https://phishtank.org/)
- [URLhaus](https://urlhaus.abuse.ch/)

## Current Features

### Visualizations
![Charts](https://user-images.githubusercontent.com/64701075/142784984-9d0d9047-633f-4ebd-a91d-e21b53fe2060.JPG)

### Live Dataset Exploration
![Dataset](https://user-images.githubusercontent.com/64701075/142784996-c6cdcf3c-c712-4e17-8b05-77a856c7e7fe.jpg)

### ML-Based Analysis
![ML](https://user-images.githubusercontent.com/64701075/142785011-7b7395a4-8565-4516-8d28-2975eec6fd88.JPG)


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
- [ ] Build and test Docker image for portability.
- [ ] Add 'About' page.
- [ ] Add 'OSINT' page.

## License

[MIT](https://choosealicense.com/licenses/mit/)


