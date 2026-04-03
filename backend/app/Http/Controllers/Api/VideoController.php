<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\Video;
use Illuminate\Http\Request;
use Illuminate\Support\Str;
use App\Services\KafkaProducer;
use Illuminate\Support\Facades\Storage;

class VideoController extends Controller
{
    public function createUpload(Request $request)
    {
        $request->validate([
            "title" => "nullable|string|max:255",
            "file_name" => "required|string",
            "content_type" => "required|string"
        ]);

        $user = $request->user();

        $video = Video::create([
            "user_id" => $user->id,
            "title" => $request->title ?? null,
            "status" => "pending",
        ]);

        $extension = pathinfo($request->file_name, PATHINFO_EXTENSION);

        $key = "videos/original/" . $video->id . "/" . Str::uuid() . "." . $extension;

        $uploadUrl = Storage::disk("s3")->temporaryUploadUrl(
            $key,
            now()->addMinutes(15),
            [
                "ContentType" => $request->content_type
            ]
        );

        $video->original_video_path = $key;
        $video->save();

        return response()->json([
            "video_id" => $video->id,
            "s3_key" => $key,
            "upload_url" => $uploadUrl,
        ]);
    }

    public function list(Request $request)
    {
        $videos = Video::where("user_id", $request->user()->id)
            ->orderBy("id", "desc")
            ->get();

        return response()->json($videos);
    }

    public function show(Request $request, $id)
    {
        $video = Video::where("id", $id)
            ->where("user_id", $request->user()->id)
            ->firstOrFail();

        return response()->json($video);
    }

    public function markUploaded(Request $request, $id, KafkaProducer $kafka)
    {
        $video = Video::where("id", $id)
            ->where("user_id", $request->user()->id)
            ->firstOrFail();

        $video->status = "processing";
        $video->save();

        $kafka->publish("video.uploaded", [
            "event" => "video.uploaded",
            "video_id" => $video->id,
            "user_id" => $video->user_id,
            "s3_key" => $video->original_video_path,
            "timestamp" => now()->toISOString()
        ]);

        return response()->json([
            "message" => "Kafka event published",
            "video" => $video
        ]);
    }

    public function getTempUrl(Video $video){
        $videoKey = $video->thumbnail_path;

        $uploadUrl = Storage::disk("s3")->temporaryUrl(
            $videoKey,
            now()->addMinutes(15),
            [
                "ResponseContentType" => 'image/jpeg',
                "ResponseContentDisposition" => 'inline'
            ]
        );

        return response()->json([
            "upload_url" => $uploadUrl,
        ]);
    }
}