# dubbio

This project is an automated YouTube Shorts generator intended for fully scheduled content pipelines. It builds AI-driven chat scenes, renders them as iMessage-style visuals, produces speech audio, composes the final video, and uploads on a defined schedule.

## Features

- **End-to-End Generation**: Creates chat scripts, profile image, visuals, and speech audio using OpenAI models.
- **iMessage Rendering Pipeline**: Uses a React UI and Playwright to capture iMessage-style chat screenshots.
- **Video Composition and Upload**: Combines assets with background video/music and uploads to YouTube Shorts.

## Prerequisites

Your environment should include:
- Python
- Node.js
- uv
- FFmpeg available in your PATH (required by MoviePy)
- An OpenAI API key
- A Google OAuth client for YouTube upload (`client_secret.json`)

## Installation and Setup

1. **Clone the Repository**:

   ```bash
   git clone https://github.com/fverri/dubbio.git
   ```

2. **Install Python Dependencies (uv)**:

   ```bash
   cd dubbio/generator
   uv venv
   .venv\Scripts\activate
   uv pip install -e .
   uv run python -m playwright install
   ```

3. **Install Frontend Dependencies**:

   ```bash
   cd ../react-imessage
   npm install
   ```

4. **Configure Secrets**:

   Create `generator/.env` with your OpenAI key:

   ```env
   OPENAI_API_KEY=your_key_here
   ```

   Place your YouTube OAuth file at `generator/client_secret.json`.

## Usage

Run the generator from the `generator` directory:

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

Feedback on the video is appreciated. Please leave a comment on the linked short.

### Configuration

Edit the schedule and limits in `generator/main.py`:

- `GENERATE_AT`: UTC time for daily generation
- `UPLOAD_TIMES`: UTC times for uploads
- `CACHE_SIZE`: Number of recent chat configurations to retain

Prompt improvements are encouraged. Modify the templates in `generator/prompts` to refine tone, structure, and output quality.

### Background Videos

Download the background videos from:

[https://drive.google.com/drive/folders/1WdyMriCtzpz-fefbO5L7g4Qxt179435A?usp=drive_link](https://drive.google.com/drive/folders/1WdyMriCtzpz-fefbO5L7g4Qxt179435A?usp=drive_link)

Place the `.mp4` files in `generator/background_videos/` (the app expects files named like `background_video_1.mp4`, `background_video_2.mp4`, etc.).

### Output

Generated videos are saved to:

```text
generator/videos/output_video_<n>.mp4
```

## Contributions

Contributions to this project are welcome. To contribute:
- Fork the repository.
- Create a new branch for your feature.
- Submit a Pull Request with your changes.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.