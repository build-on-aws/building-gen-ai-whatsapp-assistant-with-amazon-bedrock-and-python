
import boto3
from botocore.exceptions import ClientError
import io
import asyncio
import time

from amazon_transcribe.client import TranscribeStreamingClient
from amazon_transcribe.handlers import TranscriptResultStreamHandler
from amazon_transcribe.model import TranscriptEvent
from amazon_transcribe.utils import apply_realtime_delay


import logging
logger = logging.getLogger(__name__)


SAMPLE_RATE = 48000
BYTES_PER_SAMPLE = 2
CHANNEL_NUMS = 1

# Parse S3 location
CHUNK_SIZE = 1024 * 8
REGION = "us-east-1"

class MyEventHandler(TranscriptResultStreamHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.transcript = []

    async def handle_transcript_event(self, transcript_event: TranscriptEvent):
        # This handler can be implemented to handle transcriptions as needed.
        # Here's an example to get started.
        results = transcript_event.transcript.results
        for result in results:
            if result.is_partial is False:
                for alt in result.alternatives:
                    self.transcript.append(alt.transcript)
                    return alt.transcript

class TranscribeService:
    def __init__(self, ) -> None:
        self.transcribe_streaming_client = TranscribeStreamingClient(region=REGION)
        self.transcribe_client = boto3.client('transcribe', region_name=REGION)
        self.s3_client = boto3.client('s3')

    def parse_s3_location(self, s3_location):
        s3_bucket = s3_location.split('/')[2]
        s3_key = '/'.join(s3_location.split('/')[3:])
        return s3_bucket, s3_key
    
    def get_s3_object(self, s3_location):
        s3_bucket, s3_key = self.parse_s3_location(s3_location)
        return self.s3_client.get_object(Bucket=s3_bucket, Key=s3_key)
        
    async def basic_transcribe(self, s3_location,codec):
        # Start transcription to generate our async stream
        stream = await self.transcribe_streaming_client.start_stream_transcription(
            language_code="es-US",
            # language_options = ["es-US", "en-US"], # no soportado en este client
            # identify_language=True, # no soportado en este client
            media_sample_rate_hz=SAMPLE_RATE,
            media_encoding=codec,
        )

        async def write_chunks():
            response = self.get_s3_object(s3_location)
            audio_data = response['Body'].read()
            
            # Create a file-like object from the downloaded data
            audio_stream = io.BytesIO(audio_data)
            
            while True:
                chunk = audio_stream.read(CHUNK_SIZE)
                if not chunk:
                    break
                await stream.input_stream.send_audio_event(audio_chunk=chunk)
                #print("send chunk")
                #await asyncio.sleep(0)
                await asyncio.sleep(CHUNK_SIZE / (SAMPLE_RATE * BYTES_PER_SAMPLE * CHANNEL_NUMS*16))
                
            await stream.input_stream.end_stream()

        # Instantiate our handler and start processing events
        handler = MyEventHandler(stream.output_stream)
        await asyncio.gather(write_chunks(), handler.handle_events())
        return " ".join(handler.transcript)


    def transcribe(self,s3_location):
        # Time the transcription process
 
        start_time = time.time()
        
        loop = asyncio.get_event_loop()
        val = loop.run_until_complete(self.basic_transcribe(s3_location))
        #print("val:",val)
        #loop.close() # Not closing in AWS Lambda 
        
        elapsed_time = time.time() - start_time
        print(f"Transcription completed in {elapsed_time:.2f} seconds")
        
        return val
        
    def init_transcribe_job(self, s3_location, codec):
        """Initialize a new transcription job using Amazon Transcribe.
        
        Args:
            s3_location (str): The S3 URI of the audio file to transcribe
            language_code (str): The language code for transcription (default: es-US)
            
        Returns:
            dict: The response from the start_transcription_job API call
        """
        job_name = f"transcribe-{int(time.time())}"
        try:
            response = self.transcribe_client.start_transcription_job(
                TranscriptionJobName=job_name,
                Media={'MediaFileUri': s3_location},
                MediaFormat= codec,  
                IdentifyLanguage=True
            )
            return response
        except ClientError as e:
            print(f"Error starting transcription job: {str(e)}")
            raise