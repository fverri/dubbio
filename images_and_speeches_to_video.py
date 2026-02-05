import cv2
import os
import numpy as np
from moviepy import editor as mp
import tempfile
import random

TRANSITION_SEC = 0.5
ROUNDED_RADIUS = 20
GROUP_SCALE_FACTOR = 0.9


def _get_grouped_images(image_folder: str = "images"):
    image_files = [
        filename
        for filename in os.listdir(image_folder)
        if filename.lower().endswith(".png")
    ]

    groups = {}
    for image_filename in image_files:
        filename_without_extension = os.path.splitext(image_filename)[0]
        name_parts = filename_without_extension.split("_")
        if len(name_parts) < 3:
            continue

        group_key = f"{name_parts[0]}_{name_parts[1]}"
        groups.setdefault(group_key, []).append(image_filename)

    for group_key in groups:
        groups[group_key].sort(
            key=lambda filename: int(os.path.splitext(filename)[0].split("_")[-1])
        )

    ordered_keys = sorted(
        groups.keys(),
        key=lambda group_key: int(group_key.split("_")[1]),
    )
    return [(key, groups[key]) for key in ordered_keys]


def _get_ordered_speech(speech_folder: str = "speeches"):
    speech_files = sorted(
        [
            filename
            for filename in os.listdir(speech_folder)
            if filename.lower().endswith(".wav")
        ],
        key=lambda filename: int(filename.split("_")[1].split(".")[0]),
    )
    return [os.path.join(speech_folder, filename) for filename in speech_files]


def _remove_white_top_border(image: np.ndarray) -> np.ndarray:
    while image.shape[0] > 0 and np.all(image[0, :, :3] == 255):
        image = image[1:, :, :]
    return image


def _apply_rounded_corners(
    image: np.ndarray, radius: int = ROUNDED_RADIUS
) -> np.ndarray:
    height, width = image.shape[:2]
    mask = np.zeros((height, width), dtype=np.uint8)
    effective_radius = int(min(radius, width // 2, height // 2))

    cv2.rectangle(
        mask, (effective_radius, 0), (width - effective_radius, height), 255, -1
    )
    cv2.rectangle(
        mask, (0, effective_radius), (width, height - effective_radius), 255, -1
    )

    for x, y in [
        (effective_radius, effective_radius),
        (width - effective_radius, effective_radius),
        (effective_radius, height - effective_radius),
        (width - effective_radius, height - effective_radius),
    ]:
        cv2.circle(mask, (x, y), effective_radius, 255, -1)

    if image.shape[2] == 4:
        image[:, :, 3] = cv2.bitwise_and(image[:, :, 3], mask)
    else:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2BGRA)
        image[:, :, 3] = mask

    return image


def _rounded_rect_mask(width: int, height: int, radius: int) -> np.ndarray:
    mask = np.zeros((height, width), dtype=np.uint8)
    effective_radius = int(min(radius, width // 2, height // 2))

    if effective_radius <= 0:
        mask[:] = 255
        return mask.astype(np.float32) / 255.0

    cv2.rectangle(
        mask, (effective_radius, 0), (width - effective_radius, height), 255, -1
    )
    cv2.rectangle(
        mask, (0, effective_radius), (width, height - effective_radius), 255, -1
    )

    cv2.circle(mask, (effective_radius, effective_radius), effective_radius, 255, -1)
    cv2.circle(
        mask, (width - effective_radius, effective_radius), effective_radius, 255, -1
    )
    cv2.circle(
        mask, (effective_radius, height - effective_radius), effective_radius, 255, -1
    )
    cv2.circle(
        mask,
        (width - effective_radius, height - effective_radius),
        effective_radius,
        255,
        -1,
    )

    return mask.astype(np.float32) / 255.0


def images_and_speeches_to_video(video_number) -> None:
    background_video_path = (
        f"background_videos/background_video_{random.randint(1, 7)}.mp4"
    )
    image_folder = "images"
    speech_folder = "speeches"
    output_path = f"videos/output_video_{video_number}.mp4"

    capture = cv2.VideoCapture(background_video_path)
    frame_width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(capture.get(cv2.CAP_PROP_FPS)) or 30

    grouped_images = _get_grouped_images(image_folder)
    ordered_speech_paths = _get_ordered_speech(speech_folder)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_video_file:
        temp_video_path = temp_video_file.name

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    video_writer = cv2.VideoWriter(
        temp_video_path, fourcc, fps, (frame_width, frame_height)
    )

    speech_audio_clips = []
    flat_image_index = 0

    notification_clip = mp.AudioFileClip("notification.mp3")

    def _read_background_frame_loop():
        success, frame = capture.read()
        if not success:
            capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
            success, frame = capture.read()
        return frame

    for _, image_names_in_group in grouped_images:
        reference_name = image_names_in_group[-1]
        reference_path = os.path.join(image_folder, reference_name)
        reference_image = cv2.imread(reference_path, cv2.IMREAD_UNCHANGED)
        reference_image = _remove_white_top_border(reference_image)
        reference_height, reference_width = reference_image.shape[:2]

        group_scale = (
            min(frame_width / reference_width, frame_height / reference_height)
            * GROUP_SCALE_FACTOR
        )
        reference_new_width = int(reference_width * group_scale)
        reference_new_height = int(reference_height * group_scale)
        y_anchor = (frame_height - reference_new_height) // 2

        prepared_images = []
        for image_name in image_names_in_group:
            image_path = os.path.join(image_folder, image_name)
            image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
            image = _remove_white_top_border(image)
            image_height, image_width = image.shape[:2]
            new_width = int(image_width * group_scale)
            new_height = int(image_height * group_scale)
            image = cv2.resize(
                image, (new_width, new_height), interpolation=cv2.INTER_AREA
            )
            image = _apply_rounded_corners(image)

            if image.shape[2] == 4:
                alpha_channel = image[:, :, 3].astype(np.float32) / 255.0
                bgr_channels = image[:, :, :3].astype(np.float32)
            else:
                alpha_channel = np.ones((new_height, new_width), dtype=np.float32)
                bgr_channels = image[:, :, :3].astype(np.float32)

            prepared_images.append(
                {
                    "bgr": bgr_channels,
                    "alpha": alpha_channel,
                    "width": new_width,
                    "height": new_height,
                }
            )

        for index_in_group in range(len(prepared_images)):
            current_image_data = prepared_images[index_in_group]

            if flat_image_index < len(ordered_speech_paths):
                speech_clip = mp.AudioFileClip(ordered_speech_paths[flat_image_index])
                duration_frames = int(speech_clip.duration * fps)
                segment_duration = speech_clip.duration

                notification_subclip = notification_clip.subclip(
                    0, min(notification_clip.duration, segment_duration)
                )
                segment_audio_clip = mp.CompositeAudioClip(
                    [speech_clip, notification_subclip]
                )
            else:
                duration_frames = fps * 2
                segment_duration = duration_frames / fps
                silent_audio_clip = mp.AudioClip(
                    lambda t: 0, duration=segment_duration, fps=44100
                )

                notification_subclip = notification_clip.subclip(
                    0, min(notification_clip.duration, segment_duration)
                )
                segment_audio_clip = mp.CompositeAudioClip(
                    [silent_audio_clip, notification_subclip]
                )

            speech_audio_clips.append(segment_audio_clip)
            remaining_frames = duration_frames

            if index_in_group > 0:
                previous_image_data = prepared_images[index_in_group - 1]
                if current_image_data["height"] > previous_image_data["height"]:
                    transition_frame_count = min(
                        int(TRANSITION_SEC * fps), duration_frames
                    )
                    if transition_frame_count > 0:
                        crop_width = min(
                            previous_image_data["width"], current_image_data["width"]
                        )
                        x_start = (current_image_data["width"] - crop_width) // 2
                        x_offset_frame = (frame_width - crop_width) // 2
                        y_offset = y_anchor

                        min_height = min(
                            previous_image_data["height"],
                            current_image_data["height"],
                        )
                        target_height = current_image_data["height"]

                        for t in range(transition_frame_count):
                            ratio = (t + 1) / transition_frame_count
                            ratio = ratio * ratio * (3.0 - 2.0 * ratio)
                            visible_height = int(
                                round(min_height + (target_height - min_height) * ratio)
                            )

                            valid_height = min(visible_height, frame_height - y_offset)
                            valid_width = min(crop_width, frame_width - x_offset_frame)

                            frame = _read_background_frame_loop().astype(np.float32)

                            overlay_bgr = current_image_data["bgr"][
                                0:valid_height, x_start : x_start + valid_width, :
                            ]
                            overlay_alpha_cropped = current_image_data["alpha"][
                                0:valid_height, x_start : x_start + valid_width
                            ]
                            rounded_mask = _rounded_rect_mask(
                                valid_width, valid_height, ROUNDED_RADIUS
                            )
                            overlay_alpha = (overlay_alpha_cropped * rounded_mask)[
                                ..., None
                            ]

                            region_of_interest = frame[
                                y_offset : y_offset + valid_height,
                                x_offset_frame : x_offset_frame + valid_width,
                                :,
                            ]
                            region_of_interest[:] = (
                                region_of_interest * (1.0 - overlay_alpha)
                                + overlay_bgr * overlay_alpha
                            )

                            video_writer.write(np.clip(frame, 0, 255).astype(np.uint8))

                        remaining_frames -= transition_frame_count

            if remaining_frames > 0:
                x_offset_full = (frame_width - current_image_data["width"]) // 2
                y_offset = y_anchor

                valid_height_full = min(
                    current_image_data["height"], frame_height - y_offset
                )
                valid_width_full = min(
                    current_image_data["width"], frame_width - x_offset_full
                )

                for _ in range(remaining_frames):
                    frame = _read_background_frame_loop().astype(np.float32)

                    overlay_bgr_full = current_image_data["bgr"][
                        :valid_height_full, :valid_width_full, :
                    ]
                    overlay_alpha_full = current_image_data["alpha"][
                        :valid_height_full, :valid_width_full
                    ][..., None]

                    region_of_interest_full = frame[
                        y_offset : y_offset + valid_height_full,
                        x_offset_full : x_offset_full + valid_width_full,
                        :,
                    ]
                    region_of_interest_full[:] = (
                        region_of_interest_full * (1.0 - overlay_alpha_full)
                        + overlay_bgr_full * overlay_alpha_full
                    )

                    video_writer.write(np.clip(frame, 0, 255).astype(np.uint8))

            flat_image_index += 1

    capture.release()
    video_writer.release()

    final_video_clip = mp.VideoFileClip(temp_video_path, verbose=False).without_audio()

    background_music_clip = mp.AudioFileClip("background_music.mp3")
    loops_needed = int(
        np.ceil(final_video_clip.duration / background_music_clip.duration)
    )
    background_audio_clip = mp.concatenate_audioclips(
        [background_music_clip] * loops_needed
    ).subclip(0, final_video_clip.duration)

    if speech_audio_clips:
        final_speech_audio = mp.concatenate_audioclips(speech_audio_clips)
        composite_audio = mp.CompositeAudioClip(
            [final_speech_audio, background_audio_clip.volumex(0.15)]
        )
    else:
        composite_audio = background_audio_clip

    final_video_clip = final_video_clip.set_audio(composite_audio)

    final_video_clip.write_videofile(
        output_path, codec="libx264", audio_codec="aac", verbose=False, logger=None
    )
    os.remove(temp_video_path)