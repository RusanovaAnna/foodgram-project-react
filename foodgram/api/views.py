from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken

from recipes.models import Tag, Recipe, FavouriteRecipe, Ingredient, IngredientList
from users.models import User
from users.serializers import UserSerializer

from foodgram.settings import EMAIL_ADMIN

from .filtres import RecipeFilter
#from .mixins import ListCreateDestroyViewSet
from .permissions import (IsAuthorOrReadOnly,)
from .serializers import (FavoriteRecipeSerializer, GetConfirmationCode,
                          GetTokenSerializer, RecipeSerializer,
                          TagSerializer, IngredientSerializer)


@api_view(['POST'])
@permission_classes([AllowAny],)
def get_confirmation_code(request):
    serializer = GetConfirmationCode(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    username = serializer.validated_data.get('username')
    user = get_object_or_404(User, username=username)
    confirmation_code = default_token_generator.make_token(user)
    send_mail(
        'Title: Please, use it code for generate token',
        f'{confirmation_code}',
        EMAIL_ADMIN,
        [serializer.validated_data['email']],
        fail_silently=False,
    )
    return Response(serializer.validated_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny],)
def get_token(request):
    serializer = GetTokenSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = get_object_or_404(
        User, username=serializer.validated_data.get('username'))
    token = AccessToken.for_user(user)
    return Response({'token': str(token)}, status=status.HTTP_200_OK)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = (TagSerializer,)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    filter_backends = (RecipeFilter,)
    serializer_class = (RecipeSerializer,)
    permission_classes = (IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly,)

    @staticmethod
    def add_or_delete(request, model, serializer, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method != 'POST':
            get_object_or_404(
                model,
                user=request.user,
                recipe=recipe,
            ).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = serializer(
            data={'user': request.user.id, 'recipe': pk},
            context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


    @action(
        detail=False,
        methods=['get', 'delete'],
        permission_classes=[IsAuthenticated],
        serializer_class=[FavoriteRecipeSerializer],
    )
    def favorite(self, request, **kwargs):
        user = request.user
        recipes = get_object_or_404(FavouriteRecipe, id=kwargs['id'])
        fav = User.objects.filter(
            id=user.id,
            recipes=recipes
        ).exists()
        if request.method == 'GET' and not fav:
            recipes.is_favorited.add(user)
            serializer = UserSerializer(recipes)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE' and fav:
            recipes.is_favorited.remove(user)
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)
    
    @action(
        detail=False,
        methods=['get', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, **kwargs):
        user = request.user
        recipes = get_object_or_404(FavouriteRecipe, id=kwargs['id'])
        add = User.objects.filter(
            id=user.id,
            recipes=recipes
        ).exists()
        if request.method == 'GET' and not add:
            user.cart.recipes.add(recipes)
            serializer = UserSerializer(recipes)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE' and add:
            user.cart.recipes.remove(recipes)
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)


class IngredientsViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all().order_by('name')
    serializer_class = (IngredientSerializer,)

    @action(
        detail=False,
        methods=['get']
    )
    def get_shopping_cart_list(request):
        user = request.user
        list_filter = IngredientList.objects.filter(
            user_id=user.id).values_list("recipe", flat=True)
        ingredients_filter = Ingredient.objects.filter(
            recipe_id__in=list_filter).order_by('ingredient')
        ingredients = {}
        for ingredient in ingredients_filter:
            if ingredient.ingredient in ingredients.keys():
                ingredients[ingredient.ingredient] += ingredient.amount
            else:
                ingredients[ingredient.ingredient] = ingredient.amount

        shopping_list = []
        for n, m in ingredients.items():
            shopping_list.append(f'{n.title} - {m} {n.dimension} \n')
        shopping_list.append('\n\n\n\n')
        shopping_list.append('foodgram')

        response = HttpResponse(shopping_list, 'Content-Type: text/plain')
        response['Content-Disposition'] = 'attachment; filename="wishlist.txt"'
        return response


#class APIChange_Password(APIView):
#    def post(self, request, *args, **kwargs):
#        serializer = PasswordSerializer(data=request.data)
#        if serializer.is_valid():
#            data = request.data
#            password = data['current_password'] 
#            user = User.objects.get(password=password)
#            if not user.check_password(serializer.data.get('current_password')):
#                return Response({'current_password': ['Wrong password.']}, 
#                                status=status.HTTP_400_BAD_REQUEST)
#            user.set_password(serializer.data.get('new_password'))
#            user.save()
#            return Response({'status': 'password set'}, status=status.HTTP_200_OK)
#
#        return Response(serializer.errors, 
#                        status=status.HTTP_400_BAD_REQUEST)


