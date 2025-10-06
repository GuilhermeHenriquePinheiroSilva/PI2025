import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
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
  pendingCards: SoldGiftCard[] = []; // Nova lista para compras pendentes
  isLoading = true;
  revealedCodeId: string | null = null;
  hoveredRating: number = 0;

  constructor(
    private purchaseService: PurchaseService,
    private notificationService: NotificationService,
    private route: ActivatedRoute,
    private cartService: CartService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.handlePaymentStatus();
    this.loadPurchases();
  }

  private handlePaymentStatus(): void {
    this.route.queryParamMap.subscribe(params => {
      const status = params.get('status');
      const collectionStatus = params.get('collection_status');

      if (status === 'success' || status === 'approved' || collectionStatus === 'approved') {
        if (sessionStorage.getItem('paymentProcessed') !== 'true') {
          this.notificationService.show('Pagamento aprovado com sucesso!', 'success');
          this.cartService.clearCart();
          sessionStorage.setItem('paymentProcessed', 'true');
        }

        this.router.navigate([], {
          relativeTo: this.route,
          queryParams: { status: null, collection_status: null, payment_id: null, preference_id: null },
          queryParamsHandling: 'merge'
        });
      } else if (status === 'failure') {
        if (sessionStorage.getItem('paymentProcessed') !== 'true') {
          this.notificationService.show('O pagamento falhou. Tente novamente.', 'error');
          sessionStorage.setItem('paymentProcessed', 'true');
        }
        this.router.navigate([], {
          relativeTo: this.route,
          queryParams: { status: null },
          queryParamsHandling: 'merge'
        });
      }

      if (!status) {
        sessionStorage.removeItem('paymentProcessed');
      }
    });
  }

  loadPurchases(): void {
    this.isLoading = true;
    this.purchaseService.getMyPurchases().subscribe({
      next: (data) => {
        // Filtra e separa as compras por status
        this.purchasedCards = data.filter(card => card.status !== 'PENDING');
        this.pendingCards = data.filter(card => card.status === 'PENDING');
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

   rateProduct(card: SoldGiftCard, rating: number): void {
    if (card.nota) {
      this.notificationService.show('Este item já foi avaliado.', 'warning');
      return;
    }

    this.purchaseService.rateGiftCard(card.id, rating).subscribe({
      next: (response) => {
        this.notificationService.show(response.message, 'success');
        // Atualiza a nota no objeto local para a UI refletir a mudança
        card.nota = rating;
      },
      error: (err) => {
        const errorMessage = err.error?.detail || 'Não foi possível enviar a avaliação.';
        this.notificationService.show(errorMessage, 'error');
      }
    });
  }

  setHoveredRating(rating: number): void {
    this.hoveredRating = rating;
  }
}