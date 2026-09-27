package Xhamster;

/* JADX INFO: compiled from: Xhamster.kt */
/* JADX INFO: loaded from: classes.dex */
@kotlin.Metadata(d1 = {"\u0000&\n\u0002\u0018\u0002\n\u0002\u0010\u0000\n\u0000\n\u0002\u0018\u0002\n\u0002\b\u0007\n\u0002\u0010\u000b\n\u0002\b\u0002\n\u0002\u0010\b\n\u0000\n\u0002\u0010\u000e\n\u0000\b\u0086\b\u0018\u00002\u00020\u0001B\u0013\u0012\n\b\u0002\u0010\u0002\u001a\u0004\u0018\u00010\u0003¢\u0006\u0004\b\u0004\u0010\u0005J\u000b\u0010\b\u001a\u0004\u0018\u00010\u0003HÆ\u0003J\u0015\u0010\t\u001a\u00020\u00002\n\b\u0002\u0010\u0002\u001a\u0004\u0018\u00010\u0003HÆ\u0001J\u0014\u0010\n\u001a\u00020\u000b2\b\u0010\f\u001a\u0004\u0018\u00010\u0001HÖ\u0083\u0004J\n\u0010\r\u001a\u00020\u000eHÖ\u0081\u0004J\n\u0010\u000f\u001a\u00020\u0010HÖ\u0081\u0004R\u0013\u0010\u0002\u001a\u0004\u0018\u00010\u0003¢\u0006\b\n\u0000\u001a\u0004\b\u0006\u0010\u0007¨\u0006\u0011"}, d2 = {"LXhamster/HlsSources;", "", "h264", "LXhamster/HlsSource;", "<init>", "(LXhamster/HlsSource;)V", "getH264", "()LXhamster/HlsSource;", "component1", "copy", "equals", "", "other", "hashCode", "", "toString", "", "Xhamster"}, k = 1, mv = {2, 3, 0}, xi = 48)
public final /* data */ class HlsSources {

    @org.jetbrains.annotations.Nullable
    private final Xhamster.HlsSource h264;

    /* JADX WARN: Illegal instructions before constructor call */
    public HlsSources() {
        Xhamster.HlsSource hlsSource = null;
        this(hlsSource, 1, hlsSource);
    }

    public static /* synthetic */ Xhamster.HlsSources copy$default(Xhamster.HlsSources hlsSources, Xhamster.HlsSource hlsSource, int i, java.lang.Object obj) {
        if ((i & 1) != 0) {
            hlsSource = hlsSources.h264;
        }
        return hlsSources.copy(hlsSource);
    }

    @org.jetbrains.annotations.Nullable
    /* JADX INFO: renamed from: component1, reason: from getter */
    public final Xhamster.HlsSource getH264() {
        return this.h264;
    }

    @org.jetbrains.annotations.NotNull
    public final Xhamster.HlsSources copy(@org.jetbrains.annotations.Nullable Xhamster.HlsSource h264) {
        return new Xhamster.HlsSources(h264);
    }

    public boolean equals(@org.jetbrains.annotations.Nullable java.lang.Object other) {
        if (this == other) {
            return true;
        }
        return (other instanceof Xhamster.HlsSources) && kotlin.jvm.internal.Intrinsics.areEqual(this.h264, ((Xhamster.HlsSources) other).h264);
    }

    public int hashCode() {
        if (this.h264 == null) {
            return 0;
        }
        return this.h264.hashCode();
    }

    @org.jetbrains.annotations.NotNull
    public java.lang.String toString() {
        return "HlsSources(h264=" + this.h264 + ')';
    }

    public HlsSources(@org.jetbrains.annotations.Nullable Xhamster.HlsSource h264) {
        this.h264 = h264;
    }

    public /* synthetic */ HlsSources(Xhamster.HlsSource hlsSource, int i, kotlin.jvm.internal.DefaultConstructorMarker defaultConstructorMarker) {
        this((i & 1) != 0 ? null : hlsSource);
    }

    @org.jetbrains.annotations.Nullable
    public final Xhamster.HlsSource getH264() {
        return this.h264;
    }
}
