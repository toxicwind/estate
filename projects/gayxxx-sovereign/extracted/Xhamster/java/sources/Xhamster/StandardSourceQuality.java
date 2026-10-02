package Xhamster;

/* JADX INFO: compiled from: Xhamster.kt */
/* JADX INFO: loaded from: classes.dex */
@kotlin.Metadata(d1 = {"\u0000\"\n\u0002\u0018\u0002\n\u0002\u0010\u0000\n\u0000\n\u0002\u0010\u000e\n\u0002\b\n\n\u0002\u0010\u000b\n\u0002\b\u0002\n\u0002\u0010\b\n\u0002\b\u0002\b\u0086\b\u0018\u00002\u00020\u0001B\u001f\u0012\n\b\u0002\u0010\u0002\u001a\u0004\u0018\u00010\u0003\u0012\n\b\u0002\u0010\u0004\u001a\u0004\u0018\u00010\u0003¢\u0006\u0004\b\u0005\u0010\u0006J\u000b\u0010\n\u001a\u0004\u0018\u00010\u0003HÆ\u0003J\u000b\u0010\u000b\u001a\u0004\u0018\u00010\u0003HÆ\u0003J!\u0010\f\u001a\u00020\u00002\n\b\u0002\u0010\u0002\u001a\u0004\u0018\u00010\u00032\n\b\u0002\u0010\u0004\u001a\u0004\u0018\u00010\u0003HÆ\u0001J\u0014\u0010\r\u001a\u00020\u000e2\b\u0010\u000f\u001a\u0004\u0018\u00010\u0001HÖ\u0083\u0004J\n\u0010\u0010\u001a\u00020\u0011HÖ\u0081\u0004J\n\u0010\u0012\u001a\u00020\u0003HÖ\u0081\u0004R\u0013\u0010\u0002\u001a\u0004\u0018\u00010\u0003¢\u0006\b\n\u0000\u001a\u0004\b\u0007\u0010\bR\u0013\u0010\u0004\u001a\u0004\u0018\u00010\u0003¢\u0006\b\n\u0000\u001a\u0004\b\t\u0010\b¨\u0006\u0013"}, d2 = {"LXhamster/StandardSourceQuality;", "", "quality", "", "url", "<init>", "(Ljava/lang/String;Ljava/lang/String;)V", "getQuality", "()Ljava/lang/String;", "getUrl", "component1", "component2", "copy", "equals", "", "other", "hashCode", "", "toString", "Xhamster"}, k = 1, mv = {2, 3, 0}, xi = 48)
public final /* data */ class StandardSourceQuality {

    @org.jetbrains.annotations.Nullable
    private final java.lang.String quality;

    @org.jetbrains.annotations.Nullable
    private final java.lang.String url;

    /* JADX WARN: Illegal instructions before constructor call */
    public StandardSourceQuality() {
        java.lang.String str = null;
        this(str, str, 3, str);
    }

    public static /* synthetic */ Xhamster.StandardSourceQuality copy$default(Xhamster.StandardSourceQuality standardSourceQuality, java.lang.String str, java.lang.String str2, int i, java.lang.Object obj) {
        if ((i & 1) != 0) {
            str = standardSourceQuality.quality;
        }
        if ((i & 2) != 0) {
            str2 = standardSourceQuality.url;
        }
        return standardSourceQuality.copy(str, str2);
    }

    @org.jetbrains.annotations.Nullable
    /* JADX INFO: renamed from: component1, reason: from getter */
    public final java.lang.String getQuality() {
        return this.quality;
    }

    @org.jetbrains.annotations.Nullable
    /* JADX INFO: renamed from: component2, reason: from getter */
    public final java.lang.String getUrl() {
        return this.url;
    }

    @org.jetbrains.annotations.NotNull
    public final Xhamster.StandardSourceQuality copy(@org.jetbrains.annotations.Nullable java.lang.String quality, @org.jetbrains.annotations.Nullable java.lang.String url) {
        return new Xhamster.StandardSourceQuality(quality, url);
    }

    public boolean equals(@org.jetbrains.annotations.Nullable java.lang.Object other) {
        if (this == other) {
            return true;
        }
        if (!(other instanceof Xhamster.StandardSourceQuality)) {
            return false;
        }
        Xhamster.StandardSourceQuality standardSourceQuality = (Xhamster.StandardSourceQuality) other;
        return kotlin.jvm.internal.Intrinsics.areEqual(this.quality, standardSourceQuality.quality) && kotlin.jvm.internal.Intrinsics.areEqual(this.url, standardSourceQuality.url);
    }

    public int hashCode() {
        return ((this.quality == null ? 0 : this.quality.hashCode()) * 31) + (this.url != null ? this.url.hashCode() : 0);
    }

    @org.jetbrains.annotations.NotNull
    public java.lang.String toString() {
        return "StandardSourceQuality(quality=" + this.quality + ", url=" + this.url + ')';
    }

    public StandardSourceQuality(@org.jetbrains.annotations.Nullable java.lang.String quality, @org.jetbrains.annotations.Nullable java.lang.String url) {
        this.quality = quality;
        this.url = url;
    }

    public /* synthetic */ StandardSourceQuality(java.lang.String str, java.lang.String str2, int i, kotlin.jvm.internal.DefaultConstructorMarker defaultConstructorMarker) {
        this((i & 1) != 0 ? null : str, (i & 2) != 0 ? null : str2);
    }

    @org.jetbrains.annotations.Nullable
    public final java.lang.String getQuality() {
        return this.quality;
    }

    @org.jetbrains.annotations.Nullable
    public final java.lang.String getUrl() {
        return this.url;
    }
}
