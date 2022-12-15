## THIS PROJECT WAS ORIGINALLY CREATED BY [towner-10](https://github.com/towner-10)
### The program was adapted and altered for the use of Northern Tornadoes Project

<div id="top"></div>

<div align="center">
  <h3 align="center">T16 Crowd API</h3>

  <p align="center">
    Backend API for T16 Crowd project for Tornado related events on social media
    <br />
  </p>
</div>

<!-- GETTING STARTED -->
## Getting Started

To get started, follow the instructions below to get the project all setup on your local system or distribution machine. Make sure you have the correction version of python installed before running the project and you have a Mongo database all setup.

### Prerequisites

This project uses python and the latest python version should be installed
* python 3.10 on Linux
    ```sh
    sudo apt-get install python3.10
    ```

### Installation

1. Create a Mongo database with authentication
2. Clone the repo
    ```sh
    git clone https://github.com/towner-10/t16-crowd-api
    ```
3. Install PIP packages
    ```sh
    pip install -r requirements.txt
    ```
4. Enter your API in `.env`
    ```
    MONGODB_HOST="address:port"
    MONGODB_USER="username"
    MONGODB_PASS="password"
    ```

<p align="right">(<a href="#top">back to top</a>)</p>
