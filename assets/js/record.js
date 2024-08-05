window.AudioContext = window.AudioContext || window.webkitAudioContext;
    navigator.getUserMedia = navigator.getUserMedia || navigator.webkitGetUserMedia || navigator.mozGetUserMedia || navigator.msGetUserMedia;
    window.URL = window.URL || window.webkitURL;

		let getBrowser = () => {
			console.log('function getBrowser() {');
			var nVer = navigator.appVersion;
			var nAgt = navigator.userAgent;
			var browserName  = navigator.appName;
			var fullVersion  = ''+parseFloat(navigator.appVersion);
			var majorVersion = parseInt(navigator.appVersion,10);
			var nameOffset,verOffset,ix;

			// In Opera, the true version is after "Opera" or after "Version"
			if ((verOffset=nAgt.indexOf("Opera"))!=-1) {
			browserName = "Opera";
			fullVersion = nAgt.substring(verOffset+6);
			if ((verOffset=nAgt.indexOf("Version"))!=-1)
					fullVersion = nAgt.substring(verOffset+8);
			}
			// In MSIE, the true version is after "MSIE" in userAgent
			else if ((verOffset=nAgt.indexOf("MSIE"))!=-1) {
			browserName = "Microsoft Internet Explorer";
			fullVersion = nAgt.substring(verOffset+5);
			}
			// In Chrome, the true version is after "Chrome"
			else if ((verOffset=nAgt.indexOf("Chrome"))!=-1) {
				browserName = "Chrome";
				fullVersion = nAgt.substring(verOffset+7);
			}
			// In Safari, the true version is after "Safari" or after "Version"
			else if ((verOffset=nAgt.indexOf("Safari"))!=-1) {
				browserName = "Safari";
				fullVersion = nAgt.substring(verOffset+7);
				if ((verOffset=nAgt.indexOf("Version"))!=-1)
					fullVersion = nAgt.substring(verOffset+8);
			}
			// In Firefox, the true version is after "Firefox"
			else if ((verOffset=nAgt.indexOf("Firefox"))!=-1) {
				browserName = "Firefox";
				fullVersion = nAgt.substring(verOffset+8);
			}
			// In most other browsers, "name/version" is at the end of userAgent
			else if ( (nameOffset=nAgt.lastIndexOf(' ')+1) < (verOffset=nAgt.lastIndexOf('/')) ) {
			browserName = nAgt.substring(nameOffset,verOffset);
			fullVersion = nAgt.substring(verOffset+1);
			if (browserName.toLowerCase()==browserName.toUpperCase()) {
				browserName = navigator.appName;
			}
			}
			// trim the fullVersion string at semicolon/space if present
			if ((ix=fullVersion.indexOf(";"))!=-1)
				fullVersion=fullVersion.substring(0,ix);
			if ((ix=fullVersion.indexOf(" "))!=-1)
				fullVersion=fullVersion.substring(0,ix);

			majorVersion = parseInt(''+fullVersion,10);
			if (isNaN(majorVersion)) {
				fullVersion  = ''+parseFloat(navigator.appVersion);
				majorVersion = parseInt(navigator.appVersion,10);
			}

			return browserName;
		}

		if (typeof MediaRecorder === 'undefined' || !navigator.getUserMedia) {
			alert('MediaRecorder not supported on your browser, use Firefox 30 or Chrome 49 instead.');
		}

		if (getBrowser() == "Chrome") {
			console.log('if Chrome');
			var constraints = {"audio": true, "video": {  "mandatory": {  "minWidth": 640,  "maxWidth": 640, "minHeight": 480,"maxHeight": 480 }, "optional": [] } }; //Chrome
		} else if (getBrowser() == "Firefox") {
			console.log('else Firefox');
			var constraints = {audio: true, video: { width: { min: 640, ideal: 640, max: 640 },  height: { min: 480, ideal: 480, max: 480 } } }; //Firefox
		} else {
			console.log('else Chrome');
			var constraints = {"audio": true, "video": false };//Chrome
		}

		function hasClass(element, className) {
		    return (' ' + element.className + ' ').indexOf(' ' + className+ ' ') > -1;
		}

		let shouldStop;
		let stopped;
		let mediaRecorder;
		let recording = false;
		let isRecorded = false;
		let audio = document.querySelector('audio');
		let downloadLink = document.getElementById('download');
		let startBtn = document.getElementById('startRecording');
		let fd = new FormData();
		
		let voicePopup = $("#voicePopup");
		let sendVoiceButton = document.getElementById("sendVoiceButton");

		let req = new XMLHttpRequest();

		let alert = $(".alert");
		alert.hide();

		let secondCounter = 0;

		let secondsStart = 0;
		let secondsToStop = 10;





		let handleSuccess = (stream) => {
			let options;
			let recordedChunks = [];
			shouldStop = false;
			stopped = false;


			if (typeof MediaRecorder.isTypeSupported == 'function'){
				if (MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) {
					options = {mimeType: 'audio/webm;codecs=opus'};
				} else if (MediaRecorder.isTypeSupported('audio/ogg;codecs=opus')) {
					options = {mimeType: 'audio/ogg;codecs=opus'};
				}
				console.log('mimeType: '+options.mimeType);
				mediaRecorder = new MediaRecorder(stream, options);
			} else {
				console.log('mimeType DEFAULT');
				mediaRecorder = new MediaRecorder(stream);
			}

			//startBtn.setAttribute('disabled', true);
			//stopBtn.removeAttribute('disabled');
			mediaRecorder.start(10);

			//While Recording
			mediaRecorder.addEventListener('dataavailable', function(e) {
				if (e.data.size > 0) {
					recordedChunks.push(e.data);

					if (recording){
						secondCounter++;
						secondsStart = Math.floor(secondCounter/16.5);
						console.log(secondsStart);
					}

				}
				if(shouldStop === true && stopped === false) {
					console.log('Stop');
					//stopBtn.setAttribute('disabled', true);
					startBtn.removeAttribute('disabled');
					mediaRecorder.stop();
					stream.getAudioTracks().forEach(function (track) {
						track.stop();
					});
					stopped = true;
					document.getElementById("startRecording").innerHTML = "Record";
					document.getElementById("audio").removeAttribute('hidden');
				}

			});

			// Start
			mediaRecorder.addEventListener('start', function(e) {
				console.log('Started, state = ' + mediaRecorder.state);
				document.getElementById("startRecording").innerHTML = "Speak Now! (click to stop)"
				document.getElementById("audio").setAttribute('hidden', true);
				sendVoiceButton.disabled = true;
			});

			function stop(){
				sendVoiceButton.disabled = false;
				isRecorded = true;
				const audioBlob = new Blob(recordedChunks, {"type": "audio/mp3"});
				audioBlobUrl = URL.createObjectURL(new Blob(recordedChunks, {'type':'audio/mp3'}));
				audio.src = audioBlobUrl;
				downloadLink.href = audioBlobUrl;
				downloadLink.download = '{{user}}.wav';
				downloadLink.classList.remove('hide');
				
				fd.set('file', audioBlob, "audioToSave.mp3");
				fd.set('voiceMessageDetect', "hidden");
				//fetch("/audio", {"method":"POST","body":fd})
				console.log(fd);


			}

			// Stop
			mediaRecorder.addEventListener('stop', function() {
				stop();
			});


			mediaRecorder.addEventListener('warning', function(e) {
				log('Warning: ' + e);
			});

			mediaRecorder.addEventListener('error', evt => {
				console.log(evt);
				reject(evt);
			});
		};

		function sendVoiceMessage(user){
			req.open("POST", "/message/".concat("",user))
			req.onreadystatechange = function() { // listen for state changes
			  if (req.readyState == 4 && req.status == 200 && isRecorded == true) { // when completed we can move away
			    window.location = "/success?user=".concat("", user); 
			  }
			}
			descriptionInput = document.getElementById("descriptionInput").value
			// Prevent user from sending voice message without recording.

			if (isRecorded){
				if (descriptionInput.trim() == null || descriptionInput.trim() == ""){
					alert.text("Please fill the description/title field and make it atleast 5 characters..")
					alert.show();
				}
				else if (descriptionInput.trim().length >= 5){
					fd.set('descriptionInput', document.getElementById("descriptionInput").value)
					req.send(fd);
				}
			}
			else if (!isRecorded){

				alert.text("Can't send voice messsage. (record first)")
				alert.show();
			}
		}



		let errorCallback = (error) => {
			alert(error);
			console.log('navigator.getUserMedia error: ', error);	
		};

		let modal = bootstrap.Modal.getOrCreateInstance(document.getElementById('voicePopup')) // Returns a Bootstrap modal instance
		$('#voicePopup').on('hidden.bs.modal', function (e) {
			if (recording){
				console.log("Recording stopped.");
				mediaRecorder.stop();
				stream.getAudioTracks().forEach(function (track) {
					track.stop();
				});
				shouldStop = true;
				recording = false;

			}
		 
		})

		startBtn.addEventListener('click', () => {
			if (!recording){
				navigator.getUserMedia({"audio": true, "video": false}, handleSuccess, errorCallback);
				recording = true;
			}
			else {
				shouldStop = true;
				recording = false;
			}
		});

