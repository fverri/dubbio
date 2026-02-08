# dubbio

This project is an automated YouTube Shorts generator intended for fully scheduled content pipelines. It builds AI-driven chat scenes, renders them as iMessage-style visuals, produces speech audio, composes the final video, and uploads on a defined schedule.

## Features

- **End-to-End Generation**: Creates chat scripts, profile image, visuals, and speech audio using OpenAI models.
- **iMessage Rendering Pipeline**: Uses a React UI and Playwright to capture iMessage-style chat screenshots.
- **Video Composition and Upload**: Combines assets with background video/music and uploads to YouTube Shorts.

## Project Structure

- `main.py`: Orchestrates generation, scheduling, and upload.
- `chat_to_images.py`, `chat_to_speeches.py`, `images_and_speeches_to_video.py`: Asset pipeline.
- `prompts/`: Prompt templates for JSON, images, and YouTube metadata.
- `react_imessage/`: React app that renders iMessage-style chats and Playwright captures the screenshots.
- `background_videos/`, `background_music.mp3`: Stock assets for the final video.
- `images/`, `speeches/`, `videos/`: Generated assets and output videos.

## Prerequisites

Your should have:
- Python
- Node.js
- uv
- FFmpeg available in your PATH (required by MoviePy)
- An OpenAI API key
- A Google OAuth client for YouTube upload (`client_secret.json`)

### Install uv

Install uv using one of the following:

**Windows (PowerShell)**

```powershell
irm https://astral.sh/uv/install.ps1 | iex
```

**macOS/Linux**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

After installing, restart your terminal and verify:

```bash
uv --version
```

## Installation and Setup

1. **Clone the Repository**:

   ```bash
   git clone https://github.com/fverri/dubbio.git
   ```

2. **Install Python Dependencies (uv)**:

   ```bash
   cd dubbio
   ```

   ```bash
   uv sync
   ```

   ```bash
   uv run python -m playwright install
   ```

3. **Install Frontend Dependencies**:

   ```bash
   cd react_imessage
   ```

   ```bash
   npm install
   ```

   If npm reports vulnerabilities, run:

   ```bash
   npm audit fix
   ```

4. **Configure Secrets**:

   Create `.env` at the repository root with your OpenAI key:

   ```env
   OPENAI_API_KEY=your_key_here
   ```

   Place your YouTube OAuth file at `client_secret.json`.
   A walkthrough for obtaining `client_secret.json` is available at https://www.youtube.com/watch?v=sp3qM2URcig.

## Usage

Run the generator from the repository root:

```bash
uv run python main.py
```

The script will:
- Start the React renderer
- Wait until the scheduled generation time
- Generate assets and videos
- Upload each video at the scheduled upload times

## Example

Watch an example generated video:

[https://www.youtube.com/shorts/Qvvjdahfhic](https://www.youtube.com/shorts/Qvvjdahfhic)

That channel is intended to currently be controlled by a Raspberry Pi 4 running this repository's code to generate and upload the shorts.

Feedback on the video is appreciated. Please leave a comment on the linked short.

### Configuration

Edit the schedule and limits in `main.py`:

- `GENERATE_AT`: UTC time for daily generation
- `UPLOAD_TIMES`: UTC times for uploads
- `CACHE_SIZE`: Number of recent chat configurations to retain

Prompt improvements are encouraged. Modify the templates in `prompts` to refine tone, structure, and output quality.

### Background Videos

Download the background videos from:

[https://drive.google.com/drive/folders/1WdyMriCtzpz-fefbO5L7g4Qxt179435A?usp=drive_link](https://drive.google.com/drive/folders/1WdyMriCtzpz-fefbO5L7g4Qxt179435A?usp=drive_link)

The files in that Drive folder are already named like `background_video_1.mp4`, `background_video_2.mp4`, etc. The app expects that naming in `background_videos/`, so place the `.mp4` files there as-is.

### Output

Generated videos are saved to:

```text
videos/output_video_<n>.mp4
```

## Contributions

Contributions to this project are welcome. To contribute:
- Fork the repository.
- Create a new branch for your feature.
- Submit a Pull Request with your changes.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
