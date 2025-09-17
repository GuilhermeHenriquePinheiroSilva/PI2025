// src/services/cart.service.ts
import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';
import { GiftCard } from './giftcard.service';
import { NotificationService } from './notification.service';

export interface CartItem {
  product: GiftCard;
  quantity: number;
}

@Injectable({
  providedIn: 'root'
})
export class CartService {
  private cartItems: CartItem[] = [];
  private cartSubject = new BehaviorSubject<CartItem[]>([]);

  public cart$: Observable<CartItem[]> = this.cartSubject.asObservable();

  constructor(private notificationService: NotificationService) {
    const savedCart = localStorage.getItem('shoppingCart');
    if (savedCart) {
      this.cartItems = JSON.parse(savedCart);
      this.cartSubject.next(this.cartItems);
    }
  }

  addToCart(product: GiftCard, quantity: number): void {
    const existingItem = this.cartItems.find(item => item.product.id === product.id);

    if (existingItem) {
      const newQuantity = existingItem.quantity + quantity;
      if (newQuantity > product.quantityavailable) {
        this.notificationService.show(`Estoque máximo (${product.quantityavailable}) atingido para este item.`, 'warning');
        existingItem.quantity = product.quantityavailable;
      } else {
        existingItem.quantity = newQuantity;
      }
    } else {
      if (quantity > product.quantityavailable) {
        this.notificationService.show(`Estoque insuficiente. Apenas ${product.quantityavailable} unidades disponíveis.`, 'warning');
        return;
      }
      this.cartItems.push({ product, quantity });
    }
    
    this.saveCart();
    this.notificationService.show(`${product.title} adicionado ao carrinho!`, 'success');
  }

  // NOVO: Método para atualizar a quantidade de um item
  updateQuantity(productId: string, newQuantity: number): void {
    const itemIndex = this.cartItems.findIndex(item => item.product.id === productId);
    if (itemIndex > -1) {
      const item = this.cartItems[itemIndex];
      if (newQuantity > item.product.quantityavailable) {
        this.notificationService.show(`Estoque máximo (${item.product.quantityavailable}) atingido.`, 'warning');
        item.quantity = item.product.quantityavailable;
      } else if (newQuantity < 1) {
        // Remove o item se a quantidade for menor que 1
        this.cartItems.splice(itemIndex, 1);
      } else {
        item.quantity = newQuantity;
      }
      this.saveCart();
    }
  }

  // NOVO: Método para remover um item completamente
  removeItem(productId: string): void {
    const itemIndex = this.cartItems.findIndex(item => item.product.id === productId);
    if (itemIndex > -1) {
      this.cartItems.splice(itemIndex, 1);
      this.saveCart();
      this.notificationService.show('Item removido do carrinho.', 'info');
    }
  }

  getCartItems(): CartItem[] {
    return this.cartItems;
  }

  clearCart(): void {
    this.cartItems = [];
    this.saveCart();
  }
  
  private saveCart(): void {
    localStorage.setItem('shoppingCart', JSON.stringify(this.cartItems));
    this.cartSubject.next(this.cartItems);
  }

}