# YouTube m3u8 Extractor

This Python script is designed to extract `m3u8` streaming links from YouTube videos using the `yt-dlp` library. It retrieves the video’s metadata, including the `m3u8` link, title, and description. The script is optimized to handle a list of video URLs or IDs, with automatic proxy support to bypass potential rate-limiting and improve reliability.

## Features

* **Proxy Support**: Automatically fetches a list of public HTTP proxies from multiple sources to avoid blocking or throttling during the scraping process.
* **Error Handling**: Includes retry logic for failed requests and attempts to extract the `m3u8` link multiple times using different proxies.
* **Progress Tracking**: Displays a progress bar for scraping multiple video URLs.
* **Caching**: Uses a cache to store proxy lists for faster subsequent runs.
* **Asynchronous Execution**: Implements asynchronous processing for fetching and validating proxies and for extracting information from multiple video URLs concurrently.
* **CLI Support**: Allows users to input YouTube video URLs or IDs via command-line arguments or prompts.

## Requirements

* Python 3.6+
* `yt-dlp` for extracting video information
* `httpx` for asynchronous HTTP requests
* `tqdm` for displaying progress bars
* `ssl` (built-in Python module) for secure connections

### Install Dependencies

```bash
pip install yt-dlp httpx tqdm
```

## How It Works

1. **Fetching Proxies**: The script fetches proxies from several public proxy list sources. It validates the proxies by testing them through a simple HTTP request.
2. **Extracting m3u8 Links**: For each video URL provided, the script uses `yt-dlp` to extract the `m3u8` stream URL along with the video title and description. If any proxy fails, it retries using another proxy.
3. **Saving Results**: The results, including the video URL, `m3u8` link, title, description, and the proxy used, are saved to a `results.json` file.

## Usage

### Command-line Interface (CLI)

To run the script via the command line, simply provide one or more YouTube video URLs or video IDs:

```bash
python scraper.py <video_url_1>,<video_url_2> ...
```

If no URLs are provided, the script will prompt you to enter YouTube video URLs or IDs interactively.

### Example

```bash
python scraper.py https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

### Interactive Mode

If no video URLs or IDs are specified on the command line, the script will ask the user to enter URLs interactively:

```bash
Enter one or more YouTube video URLs or IDs: dQw4w9WgXcQ
```

## Caching

* The proxy list is cached in `proxy_cache.json` for 24 hours. If a valid cache is available, it is used to speed up the process.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

## Contributions

Feel free to fork the repository and submit issues or pull requests for any improvements or fixes.
