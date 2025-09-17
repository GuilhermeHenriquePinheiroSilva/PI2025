// cart.component.ts
import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';

import { NavBarComponent } from '../shared/nav-bar/nav-bar.component';
import { CartService, CartItem } from '../../../services/cart.service';
import { PurchaseService } from '../../../services/purchase.service';
import { NotificationService } from '../../../services/notification.service';
import { EmptyCartComponent } from '../empty-cart/empty-cart.component';

@Component({
  selector: 'app-cart',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    NavBarComponent,
    EmptyCartComponent
  ],
  templateUrl: './cart.component.html',
  styleUrls: ['./cart.component.css']
})
export class CartComponent implements OnInit {
  cartItems: CartItem[] = [];
  totalPedido: number = 0;
  isLoading = false; // Adicionado para controlar o estado do botão

  constructor(
    private cartService: CartService,
    private purchaseService: PurchaseService,
    private notificationService: NotificationService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.cartService.cart$.subscribe(items => {
      this.cartItems = items;
      this.calcularTotal();
    });
  }

  increaseQuantity(item: CartItem): void {
    this.cartService.updateQuantity(item.product.id, item.quantity + 1);
  }

  decreaseQuantity(item: CartItem): void {
    this.cartService.updateQuantity(item.product.id, item.quantity - 1);
  }

  removeItem(item: CartItem): void {
    this.cartService.removeItem(item.product.id);
  }

  calcularTotal(): void {
    this.totalPedido = this.cartItems.reduce((total, item) => {
      return total + (item.product.valor * item.quantity);
    }, 0);
  }

  // --- LÓGICA DE FINALIZAR COMPRA 100% ATUALIZADA ---
  finalizarCompra(): void {
    if (this.cartItems.length === 0) {
      this.notificationService.show('Seu carrinho está vazio!', 'warning');
      return;
    }

    this.isLoading = true; // Desabilita o botão
    this.notificationService.show('Redirecionando para o pagamento...', 'info');

    // Chama a nova função do serviço que envia o carrinho inteiro
    this.purchaseService.createCartPreference(this.cartItems).subscribe({
      next: (response) => {
        if (response && response.init_point) {
          // Redireciona o usuário para a URL de pagamento do Mercado Pago
          window.location.href = response.init_point;
        } else {
          this.notificationService.show('Não foi possível iniciar o pagamento. Tente novamente.', 'error');
          this.isLoading = false; // Reabilita o botão em caso de erro
        }
      },
      error: (err) => {
        const errorMessage = err.error?.detail || 'Ocorreu um erro desconhecido.';
        this.notificationService.show(`Erro: ${errorMessage}`, 'error');
        this.isLoading = false; // Reabilita o botão em caso de erro
      }
    });
  }
}