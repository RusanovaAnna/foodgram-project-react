from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from djoser.views import TokenCreateView
from recipes.models import *
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from .filtres import IngredientFilter, RecipeFavoriteFilter, RecipeFilter
from .permissions import IsAuthorOrReadOnly
from .serializers import (IngredientListSerializer, IngredientSerializer,
                          RecipeSerializer, TagSerializer, FavoriteRecipeSerializer)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.select_related(
        'author'
    ).prefetch_related('ingredients').all()
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly,]
    serializer_class = RecipeSerializer
    filterset_class = RecipeFilter

    #def update(self, serializer, id=None,):
    #    if self.request.method == 'PATCH':
    #        serializer.save(author=self.request.user)
    
    #def create(request, self, serializer,):
    #    if request.method != 'POST':
    #        serializer.delete(author=self.request.user)
    #        return Response(status=status.HTTP_204_NO_CONTENT)
    #    serializer.save(author=self.request.user)
    #    return Response(serializer.data, status=status.HTTP_201_CREATED)

    #@staticmethod
    #def post(request, id, serializers):
     #   data = {'user': request.user.id, 'recipe': id}
      #  serializer = serializers(data=data, context={'request': request})
       # serializer.is_valid(raise_exception=True)
        #serializer.save()
        #return Response(serializer.data, status=status.HTTP_201_CREATED)

  #  @staticmethod
   # def delete_method(request, id, model):
    #    user = request.user
     #   recipe = get_object_or_404(Recipe, id=id)
      #  model_instance = get_object_or_404(model, user=user, recipe=recipe)
       # model_instance.delete()
        #return Response(status=status.HTTP_204_NO_CONTENT)

    
    @action(
        detail=True, 
        methods=['POST'], 
        permission_classes=[IsAuthenticated],
        url_name='favorite',
        url_path=r'(?P<id>[\d]+)/favorite',
        filterset_class=RecipeFavoriteFilter,
    )
    def favorite(self, request, **kwargs):
        user = request.user
        recipe = get_object_or_404(Recipe, id=kwargs['id'])
        like = User.objects.filter(
            id=user.id,
            favourite_recipes=recipe
        ).exists()
        if request.method == 'GET' and not like:
            recipe.who_likes_it.add(user)
            serializer = RecipeSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE' and like:
            recipe.who_likes_it.remove(user)
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'detail': 'Действие уже выполнено'},
            status=status.HTTP_400_BAD_REQUEST
        )

#        recipe = get_object_or_404(FavoriteRecipe, favorite=obj)
#        user = request.user
 #       data = {
    #       'favorite': recipe,
     #       'user': user.id
      #  }
       # serializer = FavoriteRecipeSerializer(
        #    data=data,
         #   context={'request': request}
        #)
        #if not serializer.is_valid():
         #   return Response(
          #      serializer.errors,
           #     status=status.HTTP_400_BAD_REQUEST
            #)
     #   serializer.save()
      #  return Response(serializer.data, status=status.HTTP_201_CREATED)

#    @action(
#        detail=True, 
#        methods=['DELETE'], 
#        permission_classes=[IsAuthenticated],
#        url_name='favorite',
#        url_path=r'(?P<id>[\d]+)/favorite',
#        filterset_class=RecipeFavoriteFilter,
#    )
#    def delete_favorite(self, request, id):
#        user = request.user
#        recipe = get_object_or_404(Recipe, id=id)
#        FavoriteRecipe.objects.filter(user=user, favorite=recipe).delete()
 #       return Response(status=status.HTTP_204_NO_CONTENT)

   # @action(
    #    detail=True, 
     #   methods=['POST'], 
      #  permission_classes=[IsAuthenticated],
        #url_path=r'(?P<id>[\d]+)/shopping_cart',
       # url_name='shopping_cart',
    #)
    #def shopping_cart(self, request, id):
     #   return self.post(
      #      request, 
       #     id, serializers=IngredientListSerializer,
        #)

   # @shopping_cart.mapping.delete
    #def delete_shopping_cart(self, request, id):
   #     return self.delete_method(
   #         request, id, model=IngredientList
    #    )
    #@action(
    #    detail=False,
    #    methods=['get', 'delete'],
    #    permission_classes=[IsAuthenticated],
    #    filterset_class=RecipeFavoriteFilter,
    #    url_name='favorite',
    #    url_path=r'(?P<id>[\d]+)/favorite',
    #    serializer_class=FavoriteRecipeSerializer,
    #)
    #def favorite(self, request, id):
    #    user = request.user
    #    model = FavoriteRecipe.objects.filter(user=user, recipe__id=id).exists()
    #    if request.method == 'GET' and not model:
    #        recipe=get_object_or_404(Recipe, id=id)
    #        FavoriteRecipe.objects.create(user=user, recipe=recipe)
    #        serializer = FavoriteRecipeSerializer(recipe)
    #        return Response(serializer.data, status=status.HTTP_201_CREATED)
    #    if request.method == 'DELETE' and model:
    #        FavoriteRecipe.objects.filter(user=user, recipe__id=id).delete()
     #       return Response(status=status.HTTP_204_NO_CONTENT)
     #   return Response(status=status.HTTP_400_BAD_REQUEST)
    
    @action(
        detail=False,
        methods=['get', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path=r'(?P<id>[\d]+)/shopping_cart',
        url_name='shopping_cart',
    )
    def shopping_cart(self, request, **kwargs):
        user = request.user
        recipe = get_object_or_404(Recipe, id=kwargs['id'])
        is_added = User.objects.filter(
            id=user.id,
            cart__recipes=recipe
        ).exists()
        if request.method == 'GET' and not is_added:
            user.cart.recipes.add(recipe)
            serializer = IngredientListSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE' and is_added:
            user.cart.recipes.remove(recipe)
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'detail': 'Действие уже выполнено'},
            status=status.HTTP_400_BAD_REQUEST
        )
#        in_cart = IngredientList.objects.filter(recipe__id=id).exists()
 #       if request.method == 'POST' and not in_cart:
  #          recipe=get_object_or_404(Recipe, id=id)
   #         IngredientList.objects.create(recipe__id=id)
    #        serializer = RecipeSerializer(recipe)
     #       return Response(serializer.data, status=status.HTTP_201_CREATED)
      #  if request.method == 'DELETE' and in_cart:
       #     IngredientList.objects.filter(recipe__id=id).delete()
        #    return Response(status=status.HTTP_204_NO_CONTENT)
        #return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False,
        methods=['get'],
        url_name='download_shopping_cart',
        url_path='download_shopping_cart',
    )
    def download_shopping_cart(self, request):
        user = request.user
        in_cart = Recipe.objects.filter(author=user)
        queryset = in_cart.values_list(
            'ingredients__name',
            'ingredients__measurement_unit',
        ).annotate(
            amount_sum=Sum('ingredient_list__amount')
        )
        text = 'Список покупок для вас: \n'
        for ingredient in queryset:
            text += (
                f"{list(ingredient)[0]} - "
                f"{list(ingredient)[2]} "
                f"{list(ingredient)[1]} \n"
            )
        response = HttpResponse(text, 'Content-Type: application/txt')
        response['Content-Disposition'] = 'attachment; filename="yourwishlist"'
        return response


class IngredientsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    filterset_class = IngredientFilter
    serializer_class = IngredientSerializer
    pagination_class = None
    

class CustomTokenCreateView(TokenCreateView):

    def _action(self, serializer):
        response = super()._action(serializer)
        response.status_code = status.HTTP_201_CREATED
        return response
