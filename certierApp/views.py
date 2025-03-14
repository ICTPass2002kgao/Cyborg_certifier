 
from django.conf import settings
from rest_framework.response import Response
from rest_framework.decorators import api_view,permission_classes
from rest_framework import status
from .serializers import FileSerializers  ,CertifiedDocumentSerializers, UserFaceVerificationSerializer
from rest_framework.permissions import AllowAny,IsAuthenticated
from .serializers import UserRegistrationSerializer 
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login,logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import UserFaceVerification, userDocuments ,CertifiedDocumentUpload  
from rest_framework.response import Response
from django.core.mail import EmailMessage
from django.views.decorators.csrf import csrf_exempt 
import cv2
import mimetypes
import numpy as np   
from rest_framework import status  
from sklearn.metrics.pairwise import cosine_similarity
from PIL import Image, ImageDraw, ImageFont
import io 
from insightface.app import FaceAnalysis 
from io import BytesIO 
from django.core.files.storage import default_storage
from django.conf import settings 
from fpdf import FPDF
import os
from datetime import datetime  
from django.urls import reverse
import os
 
# Assuming you have a model named UserFaceVerification
# from .models import UserFaceVerification

def verify_faces(face1_file, face2_file): 
    if face1_file is None or face2_file is None:
        print("One or both file objects are None")
        return False

    app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
    app.prepare(ctx_id=0)

    try:
        face1_img = np.array(bytearray(face1_file.read()), dtype=np.uint8)
        face1_img = cv2.imdecode(face1_img, cv2.IMREAD_COLOR)
        face1_faces = app.get(face1_img)
        if len(face1_faces) == 0:
            print(f"No face detected in the first image")
            return False

        face1_embedding = face1_faces[0].embedding

        face2_img = np.array(bytearray(face2_file.read()), dtype=np.uint8)
        face2_img = cv2.imdecode(face2_img, cv2.IMREAD_COLOR)
        face2_faces = app.get(face2_img)
        if len(face2_faces) == 0:
            print(f"No face detected in the second image")
            return False

        face2_embedding = face2_faces[0].embedding

        similarity = np.dot(face1_embedding, face2_embedding) / (
            np.linalg.norm(face1_embedding) * np.linalg.norm(face2_embedding)
        )

        print(f"Similarity score: {similarity:.2f}")
        return similarity > 0.5
    except Exception as e:
        print(f"Error in verify_faces: {str(e)}")
        return False
def merge_images_with_custom_layout(request,image1_path, image2_path, image3_path=None):
    try:
        # Open images
        id_image = Image.open(image1_path).convert("L")
        stamp_image = Image.open(image2_path).convert("L")

        # Optional third image (back image)
        if image3_path:
            id_back_image = Image.open(image3_path).convert("L")
        else:
            id_back_image = None

        # Image resizing logic
        MAX_WIDTH = 600
        MAX_HEIGHT = 400
        if id_image.width > MAX_WIDTH or id_image.height > MAX_HEIGHT:
            scale_factor = min(MAX_WIDTH / id_image.width, MAX_HEIGHT / id_image.height)
            id_image = id_image.resize((int(id_image.width * scale_factor), int(id_image.height * scale_factor)))
        
        if stamp_image.width > MAX_WIDTH or stamp_image.height > MAX_HEIGHT:
            scale_factor = min(MAX_WIDTH / stamp_image.width, MAX_HEIGHT / stamp_image.height)
            stamp_image = stamp_image.resize((int(stamp_image.width * scale_factor), int(stamp_image.height * scale_factor)))

        if id_back_image:
            if id_back_image.width > MAX_WIDTH or id_back_image.height > MAX_HEIGHT:
                scale_factor = min(MAX_WIDTH / id_back_image.width, MAX_HEIGHT / id_back_image.height)
                id_back_image = id_back_image.resize((int(id_back_image.width * scale_factor), int(id_back_image.height * scale_factor)))

        # Create the final image canvas with a white background
        canvas_width = max(id_image.width, stamp_image.width) + 100
        canvas_height = id_image.height + (id_back_image.height if id_back_image else 0) + stamp_image.height + 75
        white_bg = Image.new("RGB", (canvas_width, canvas_height), "white")

        # Place ID image
        id_x = (canvas_width - id_image.width) // 2
        id_y = 25
        white_bg.paste(id_image.convert("RGB"), (id_x, id_y))

        # Place back ID image if available
        if id_back_image:
            back_id_x = (canvas_width - id_back_image.width) // 2
            back_id_y = id_y + id_image.height + 10
            white_bg.paste(id_back_image.convert("RGB"), (back_id_x, back_id_y))
            stamp_y = back_id_y + id_back_image.height + 25
        else:
            stamp_y = id_y + id_image.height + 25

        # Place stamp image
        stamp_x = canvas_width - stamp_image.width - 50
        white_bg.paste(stamp_image.convert("RGB"), (stamp_x, stamp_y))

        # Add current date
        draw = ImageDraw.Draw(white_bg)
        current_date = datetime.now().strftime("%Y-%m-%d")
        font_size = 18
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except IOError:
            font = ImageFont.load_default()

        stamp_center_x = stamp_x + (stamp_image.width // 2)
        stamp_center_y = stamp_y + (stamp_image.height // 2)

        bbox = draw.textbbox((0, 0), current_date, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        text_x = stamp_center_x - (text_width // 2)
        text_y = stamp_center_y - (text_height // 2)

        padding = 10
        draw.rectangle([text_x - padding, text_y - padding, text_x + text_width + padding, text_y + text_height + padding], fill="white")
        draw.text((text_x, text_y), current_date, fill="black", font=font)

        # Save temporary image
        temp_image_path = "merged_image.jpg"
        white_bg.save(temp_image_path)

        # Convert to PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.image(temp_image_path, x=10, y=10, w=190)

        # Save PDF to the media directory
        pdf_output_path = os.path.join(settings.MEDIA_ROOT, 'pdfs', 'certified_document.pdf')

        os.makedirs(os.path.dirname(pdf_output_path), exist_ok=True)
        pdf.output(pdf_output_path)

        # Remove temporary image
        os.remove(temp_image_path)

        # Return the URL of the PDF
        pdf_url = request.build_absolute_uri(f"/media/pdfs/certified_document.pdf")

        print(f"PDF created and saved successfully at: {pdf_output_path}")
        return pdf_url

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None

@api_view(['POST'])
@permission_classes([AllowAny])
def verifyFace(request):
    try: 
        id_face_file = request.FILES.get('id_front_face')
        cam_face_file = request.FILES.get('recognised_face')
        id_back_face = request.FILES.get('id_back_face')
        stamp = request.FILES.get('stamp')
        email = request.POST.get('email')
 
        print(f"ID Face File: {id_face_file}")
        print(f"Camera Face File: {cam_face_file}")
        print(f"ID Back Face: {id_back_face}")
        print(f"Stamp: {stamp}")
 
        if not id_face_file or not cam_face_file:
            return Response({'error': 'Both ID and webcam face images are required.'}, status=status.HTTP_400_BAD_REQUEST)
 
        is_same = verify_faces(id_face_file, cam_face_file)

        if is_same:
            print("The faces match!")
 
            pdf = merge_images_with_custom_layout(request,id_face_file, stamp, id_back_face)
  

            # You can optionally send the PDF as an email (commented out for now)
            email_message = EmailMessage(
                subject='Your Certified Document Feedback',
                body='Please find the document attached.\n\n\n We\'re happy to work with you',
                from_email=settings.EMAIL_HOST_USER,
                to=[email]
            )

            # Uncomment to send email with PDF attachment
            # email_message.attach('Certified_ID.pdf', pdf, 'application/pdf')
            # try:
            #     email_message.send()
            #     print("Email sent successfully")
            # except Exception as e:
            #     print(f"Error occurred: {str(e)}")
            #     return Response({'error': f'An error occurred: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Create a record in the database
             
            # Return the response with the matching status and PDF URL
            return Response({
                'match': "Matched",
                'pdf_url': pdf
            }, status=status.HTTP_200_OK)
        else:
            print("The faces do NOT match!")
            return Response({'match': "Unmatched"}, status=status.HTTP_200_OK)

    except Exception as e: 
        print(f"An error occurred: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@api_view(['POST'])
def register_user(request):
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({'message': 'User created successfully!'}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

 
def home(request): 
    documents = UserFaceVerification.objects.all() 
    context = {
        'documents': documents
    }
    return render(request, 'index.html', context)


def done(request):  
    return render(request, 'done.html', ) 


@csrf_exempt
@permission_classes([AllowAny])
@api_view(['POST'])
def upload_file(request):  
    if 'file' not in request.FILES:
        return Response({'error': 'No file provided!'}, status=400)
    
    file = request.FILES['file']
    file_type = file.content_type
     
    email = request.data.get('email', None)
    address =  request.data.get('address', None)
     
    if not email:
        return Response({'error': 'Email is required!'}, status=400)
    elif not address:
        return Response({'error':'Address is Required Please Enter your address'})
    if file_type.startswith('image/'): 
        serializers = FileSerializers(data={'image': file, 'email': email,'address':address})
    elif file_type.startswith('application/pdf'): 
        serializers = FileSerializers(data={'pdf': file, 'email': email,'address':address})
    else:
        return Response({'error': 'Invalid file type. Only images and PDFs are allowed!'}, status=400)
 
    if serializers.is_valid():
        serializers.save()
        return Response(serializers.data, status=201)
 
    return Response(serializers.errors, status=400)

 
@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def upload_stamp(request):
    """
    Endpoint to upload a stamp image.
    """
    if 'file' not in request.FILES:
        return Response({'error': 'No file uploaded.'}, status=status.HTTP_400_BAD_REQUEST)

    file = request.FILES['file']
    address = request.POST['address']
    
    data = {'stamp': file,'address':address}
    serializer = CertifiedDocumentSerializers(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response({'message': 'Stamp and address uploaded successfully.', 'data': serializer.data}, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Endpoint to get the uploaded stamp
@api_view(['GET'])
@permission_classes([AllowAny])
def get_stamp(request):
    """
    Endpoint to retrieve all uploaded stamps.
    """
    stamps = CertifiedDocumentUpload.objects.all()
    serializer = CertifiedDocumentSerializers(stamps, many=True)
    return Response({'data': serializer.data}, status=status.HTTP_200_OK)

def create_stamp(request):
    
    documents = UserFaceVerification.objects.all() 
    context = {
            'documents': documents
        }
    return render(request,'index.html',context)

from django.shortcuts import render, redirect
from django.core.mail import EmailMessage
from django.conf import settings
from django.views.decorators.http import require_POST

@require_POST
def upload_certified_document(request):
    if 'file' not in request.FILES or 'email' not in request.POST:
        return render(request, 'error.html', {'error': 'No file or email provided!'})
    
    file = request.FILES['file']
    email = request.POST['email']
    file_type = file.content_type
    
    if not (file_type.startswith('image/') or file_type.startswith('application/pdf')):
        return render(request, 'error.html', {'error': 'Invalid file type. Only images and PDFs are allowed!'})

    email_message = EmailMessage(
        subject='Your Certified Document Feedback',
        body='Please find the document attached.',
        from_email=settings.EMAIL_HOST_USER,
        to=[email]
    )

    email_message.attach(file.name, file.read(), file.content_type)

    try:
        email_message.send()
        user_doc = get_object_or_404(userDocuments, email=email) 
        user_doc.delete()
        return redirect('success_url')  
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        return render(request, 'error.html', {'error': str(e)})
    
    
@csrf_exempt
def login_user(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('create_stamp')   
        else: 
            messages.error(request, 'Invalid email or password.')
            return redirect('login_user')                  

    return render(request, 'login.html')  
         
@csrf_exempt
def logout_user(request): 
    logout(request)
    return redirect('login_user')                
 
     