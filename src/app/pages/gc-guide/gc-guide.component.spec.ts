import { ComponentFixture, TestBed } from '@angular/core/testing';

import { GcGuideComponent } from './gc-guide.component';

describe('GcGuideComponent', () => {
  let component: GcGuideComponent;
  let fixture: ComponentFixture<GcGuideComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [GcGuideComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(GcGuideComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
