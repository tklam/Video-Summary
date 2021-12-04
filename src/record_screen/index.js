const start = document.getElementById("start");
const stop = document.getElementById("stop");
const download_link = document.getElementById("download_link");
let recorder, stream;

async function startRecording() {
  const gdmOptions = {
    video: {
      displaySurface: "browser",
      cursor: "never",
      logicalSurface: true
    },
    audio: {
      echoCancellation: false,
      noiseSuppression: false,
      sampleRate: 44100,
      channelCount: 2
    }
  }


  try {
  stream = await navigator.mediaDevices.getDisplayMedia( 
    gdmOptions
  );
  } catch(err) {
    console.error("Error: " + err);
  }

  recorder = new MediaRecorder(stream, {mimetype: 'video/webm'});

  const chunks = [];
  recorder.ondataavailable = e => chunks.push(e.data);
  recorder.onstop = e => {
    const completeBlob = new Blob(chunks, { type: chunks[0].type });
    video_src = URL.createObjectURL(completeBlob);
    download_link.setAttribute('href', video_src);
    download_link.download = "video.webm";
  };

  recorder.start();
}

start.addEventListener("click", () => {
  start.setAttribute("disabled", true);
  stop.removeAttribute("disabled");
  download_link.innerHTML = 'Processing...';
  download_link.setAttribute("disabled", true);

  startRecording();
});

stop.addEventListener("click", () => {
  stop.setAttribute("disabled", true);
  start.removeAttribute("disabled");

  recorder.stop();
  stream.getVideoTracks()[0].stop();

  download_link.innerHTML = 'Download now (may take a long period of time after clicking this link)';
  download_link.removeAttribute("disabled");
});

