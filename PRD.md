# Product Requirements Document: Photo Watermark 2

## 1. Introduction

This document outlines the product requirements for the Photo Watermark 2 application, a desktop tool for Windows designed for adding watermarks to images.

## 2. Core Features

### 2.1. File Handling

*   **Image Import:**
    *   Support single image import via drag-and-drop or a file selector.
    *   Support batch import of multiple images or an entire folder.
    *   Display a list of imported images with thumbnails and filenames in the UI.
*   **Supported Formats:**
    *   **Input:** Must support JPEG and PNG. PNG must support the alpha channel.
    *   **Output:** Users can choose to export as JPEG or PNG.
*   **Image Export:**
    *   Users must specify an output folder.
    *   To prevent overwriting original images, exporting to the original folder is disabled by default.
    *   Provide file naming options:
        *   Keep original filename.
        *   Add a custom prefix (e.g., `wm_`).
        *   Add a custom suffix (e.g., `_watermarked`).

### 2.2. Watermark Types

*   **Text Watermark:**
    *   **Content:** Users can input any custom text.
    *   **Transparency:** Adjustable text opacity (0-100%).

### 2.3. Watermark Layout and Style

*   **Real-time Preview:** All adjustments to the watermark (content, position, transparency, etc.) must be reflected in real-time on a preview window. Users can switch between different imported images to preview the effect.
*   **Positioning:**
    *   **Preset Positions:** Provide a 9-grid layout for one-click placement of the watermark (corners, edges, and center).
    *   **Manual Dragging:** Allow users to drag the watermark to any position on the preview image.

### 2.4. Configuration Management

*   **Watermark Templates:**
    *   Users can save the current watermark settings (content, position, transparency, etc.) as a template.
    *   Users can load, manage, and delete saved templates.
    *   The application can automatically load the last used settings or a default template on startup.

## 3. Non-functional Requirements

*   **Platform:** The application must be a native Windows application.
*   **Usability:** The user interface should be intuitive and easy to use for non-technical users.

## 4. Future (Optional) Features

The following features are considered for future releases and are not part of the initial scope:

*   **Advanced Input Formats:** Support for BMP, TIFF.
*   **Advanced Export Options:**
    *   JPEG quality/compression slider.
    *   Image resizing (by width, height, or percentage).
*   **Advanced Text Watermark Options:**
    *   Font selection (family, size, bold, italic).
    *   Color picker.
    *   Shadow or stroke effects.
*   **Image Watermark:**
    *   Import an image as a watermark.
    *   Support for PNGs with transparency.
    *   Scaling options for the image watermark.
    *   Opacity control for the image watermark.
*   **Watermark Rotation:** Ability to rotate the watermark.