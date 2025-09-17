import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router'; // Importe também o Router
import { PurchaseService, SoldGiftCard } from '../../../services/purchase.service';
import { NotificationService } from '../../../services/notification.service';
import { CartService } from '../../../services/cart.service';
import { NavBarComponent } from '../shared/nav-bar/nav-bar.component';
import { FooterComponent } from '../shared/footer/footer.component';

@Component({
  selector: 'app-my-purchases',
  standalone: true,
  imports: [CommonModule, NavBarComponent, FooterComponent],
  templateUrl: './my-purchases.component.html',
  styleUrls: ['./my-purchases.component.css']
})
export class MyPurchasesComponent implements OnInit {
  purchasedCards: SoldGiftCard[] = [];
  isLoading = true;
  revealedCodeId: string | null = null;

  constructor(
    private purchaseService: PurchaseService,
    private notificationService: NotificationService,
    private route: ActivatedRoute,
    private cartService: CartService,
    private router: Router // Injete o Router para manipular a URL
  ) {}

  ngOnInit(): void {
    this.handlePaymentStatus(); // Centraliza a lógica de tratamento do status
    this.loadPurchases();
  }

  // --- LÓGICA ATUALIZADA ---
  private handlePaymentStatus(): void {
    this.route.queryParamMap.subscribe(params => {
      const status = params.get('status');
      const collectionStatus = params.get('collection_status'); // Adicionado para robustez

      // Verifica se a URL contém um indicador de sucesso
      if (status === 'success' || status === 'approved' || collectionStatus === 'approved') {
        // Mostra a notificação apenas uma vez
        if (sessionStorage.getItem('paymentProcessed') !== 'true') {
          this.notificationService.show('Pagamento aprovado com sucesso!', 'success');
          this.cartService.clearCart();
          sessionStorage.setItem('paymentProcessed', 'true'); // Marca que já processou
        }

        // Limpa os parâmetros da URL para evitar reprocessamento no refresh
        this.router.navigate([], {
          relativeTo: this.route,
          queryParams: {
            status: null,
            collection_status: null,
            payment_id: null,
            preference_id: null
            // Adicione outros parâmetros que o MP envia para serem limpos
          },
          queryParamsHandling: 'merge'
        });

      } else if (status === 'failure') {
        if (sessionStorage.getItem('paymentProcessed') !== 'true') {
          this.notificationService.show('O pagamento falhou. Tente novamente.', 'error');
          sessionStorage.setItem('paymentProcessed', 'true');
        }
        // Limpa a URL também em caso de falha
        this.router.navigate([], {
          relativeTo: this.route,
          queryParams: { status: null },
          queryParamsHandling: 'merge'
        });
      }

      // Garante que a marcação seja limpa ao navegar para outras páginas
      if (!status) {
        sessionStorage.removeItem('paymentProcessed');
      }
    });
  }

  loadPurchases(): void {
    this.isLoading = true;
    this.purchaseService.getMyPurchases().subscribe({
      next: (data) => {
        this.purchasedCards = data;
        this.isLoading = false;
      },
      error: (err) => {
        this.notificationService.show('Erro ao carregar suas compras.', 'error');
        this.isLoading = false;
      }
    });
  }

  revealAndCopyCode(card: SoldGiftCard): void {
    navigator.clipboard.writeText(card.code).then(() => {
      this.revealedCodeId = card.id;
      this.notificationService.show(`Código "${card.code}" copiado!`, 'success');

      setTimeout(() => {
        if (this.revealedCodeId === card.id) {
          this.revealedCodeId = null;
        }
      }, 5000);
    }).catch(err => {
      console.error('Erro ao copiar código: ', err);
      this.notificationService.show('Não foi possível copiar o código.', 'error');
    });
  }
}