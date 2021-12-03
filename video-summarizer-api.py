from flask import Flask
from rq import Queue
from urllib.parse import unquote
import importlib  
import json
import redis
video_summarizer = importlib.import_module('do-single')


redis_host = 'localhost' # 'redis'


app = Flask(__name__)


# redis server
redis_server = redis.Redis(host=redis_host, port=6379)
video_summarizer_queue = Queue(connection=redis_server, default_timeout=3600)


# e.g. http://localhost:5000/enqueue/123/https%3A%2F%2Fwww.youtube.com%2Fwatch%3Fv%3DfJubafP3IMI/20/20
@app.route('/enqueue/<string:video_id>/<path:video_url>/<int:upper_similarity_threshold>/<int:lower_similarity_threshold>')
def index(video_id, video_url, upper_similarity_threshold, lower_similarity_threshold):
    args = video_summarizer.DummyArgs()
    args.video_id = video_id
    args.local_video_path = None
    args.video_url = video_url
    args.upper_similarity_threshold = upper_similarity_threshold
    args.lower_similarity_threshold = lower_similarity_threshold
    args.no_need_change_dir = False
    args.crop_width_pixel = 0
    args.crop_height_pixel = 0
    args.crop_x_offet = 0
    args.crop_y_offet = 0
    args.subtitle_lang=None
    args.run_stages=[
        video_summarizer.RunStage.Download.value,
        video_summarizer.RunStage.LocateSpeechSegments.value,
        video_summarizer.RunStage.CollectFrames.value,
        video_summarizer.RunStage.DownSampleFrames.value,
        video_summarizer.RunStage.DeduplicateFrames.value,
        video_summarizer.RunStage.GeneratePptx.value ]

    new_job = video_summarizer_queue.enqueue(video_summarizer.main, args, result_ttl=3600)

    result = {
            "enqueued_job" : {
                "video_id" : video_id,
                "job_id" : new_job.id,
                "video_url" : video_url,
                "upper_similarity_threshold" : upper_similarity_threshold,
                "lower_similarity_threshold" : lower_similarity_threshold
             }
            }

    return json.dumps(result)


# e.g. http://localhost:5000/job/123-456
@app.route('/job/<string:job_id>')
def getJob(job_id):

    res = video_summarizer_queue.fetch_job(job_id)

    if res is None or res.result is None:
        return '{}'

    return '{"enqueued_job": { ' + f'"job_id":"{new_job.id}", ' + f'"result": "{res.result}",' + f'"enqueued_at": "{res.enqueued_at}",' + f'"done_at": "{res.ended_at}"' + '}}'


if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)
