package Xhamster;

/* JADX INFO: compiled from: Xhamster.kt */
/* JADX INFO: loaded from: classes.dex */
@kotlin.Metadata(d1 = {"\u0000\"\n\u0002\u0018\u0002\n\u0002\u0010\u0000\n\u0000\n\u0002\u0010\u000e\n\u0002\b\r\n\u0002\u0010\u000b\n\u0002\b\u0002\n\u0002\u0010\b\n\u0002\b\u0002\b\u0086\b\u0018\u00002\u00020\u0001B+\u0012\n\b\u0002\u0010\u0002\u001a\u0004\u0018\u00010\u0003\u0012\n\b\u0002\u0010\u0004\u001a\u0004\u0018\u00010\u0003\u0012\n\b\u0002\u0010\u0005\u001a\u0004\u0018\u00010\u0003¢\u0006\u0004\b\u0006\u0010\u0007J\u000b\u0010\f\u001a\u0004\u0018\u00010\u0003HÆ\u0003J\u000b\u0010\r\u001a\u0004\u0018\u00010\u0003HÆ\u0003J\u000b\u0010\u000e\u001a\u0004\u0018\u00010\u0003HÆ\u0003J-\u0010\u000f\u001a\u00020\u00002\n\b\u0002\u0010\u0002\u001a\u0004\u0018\u00010\u00032\n\b\u0002\u0010\u0004\u001a\u0004\u0018\u00010\u00032\n\b\u0002\u0010\u0005\u001a\u0004\u0018\u00010\u0003HÆ\u0001J\u0014\u0010\u0010\u001a\u00020\u00112\b\u0010\u0012\u001a\u0004\u0018\u00010\u0001HÖ\u0083\u0004J\n\u0010\u0013\u001a\u00020\u0014HÖ\u0081\u0004J\n\u0010\u0015\u001a\u00020\u0003HÖ\u0081\u0004R\u0013\u0010\u0002\u001a\u0004\u0018\u00010\u0003¢\u0006\b\n\u0000\u001a\u0004\b\b\u0010\tR\u0013\u0010\u0004\u001a\u0004\u0018\u00010\u0003¢\u0006\b\n\u0000\u001a\u0004\b\n\u0010\tR\u0013\u0010\u0005\u001a\u0004\u0018\u00010\u0003¢\u0006\b\n\u0000\u001a\u0004\b\u000b\u0010\t¨\u0006\u0016"}, d2 = {"LXhamster/VideoEntity;", "", "title", "", "description", "thumbBig", "<init>", "(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;)V", "getTitle", "()Ljava/lang/String;", "getDescription", "getThumbBig", "component1", "component2", "component3", "copy", "equals", "", "other", "hashCode", "", "toString", "Xhamster"}, k = 1, mv = {2, 3, 0}, xi = 48)
public final /* data */ class VideoEntity {

    @org.jetbrains.annotations.Nullable
    private final java.lang.String description;

    @org.jetbrains.annotations.Nullable
    private final java.lang.String thumbBig;

    @org.jetbrains.annotations.Nullable
    private final java.lang.String title;

    public VideoEntity() {
        this(null, null, null, 7, null);
    }

    public static /* synthetic */ Xhamster.VideoEntity copy$default(Xhamster.VideoEntity videoEntity, java.lang.String str, java.lang.String str2, java.lang.String str3, int i, java.lang.Object obj) {
        if ((i & 1) != 0) {
            str = videoEntity.title;
        }
        if ((i & 2) != 0) {
            str2 = videoEntity.description;
        }
        if ((i & 4) != 0) {
            str3 = videoEntity.thumbBig;
        }
        return videoEntity.copy(str, str2, str3);
    }

    @org.jetbrains.annotations.Nullable
    /* JADX INFO: renamed from: component1, reason: from getter */
    public final java.lang.String getTitle() {
        return this.title;
    }

    @org.jetbrains.annotations.Nullable
    /* JADX INFO: renamed from: component2, reason: from getter */
    public final java.lang.String getDescription() {
        return this.description;
    }

    @org.jetbrains.annotations.Nullable
    /* JADX INFO: renamed from: component3, reason: from getter */
    public final java.lang.String getThumbBig() {
        return this.thumbBig;
    }

    @org.jetbrains.annotations.NotNull
    public final Xhamster.VideoEntity copy(@org.jetbrains.annotations.Nullable java.lang.String title, @org.jetbrains.annotations.Nullable java.lang.String description, @org.jetbrains.annotations.Nullable java.lang.String thumbBig) {
        return new Xhamster.VideoEntity(title, description, thumbBig);
    }

    public boolean equals(@org.jetbrains.annotations.Nullable java.lang.Object other) {
        if (this == other) {
            return true;
        }
        if (!(other instanceof Xhamster.VideoEntity)) {
            return false;
        }
        Xhamster.VideoEntity videoEntity = (Xhamster.VideoEntity) other;
        return kotlin.jvm.internal.Intrinsics.areEqual(this.title, videoEntity.title) && kotlin.jvm.internal.Intrinsics.areEqual(this.description, videoEntity.description) && kotlin.jvm.internal.Intrinsics.areEqual(this.thumbBig, videoEntity.thumbBig);
    }

    public int hashCode() {
        return ((((this.title == null ? 0 : this.title.hashCode()) * 31) + (this.description == null ? 0 : this.description.hashCode())) * 31) + (this.thumbBig != null ? this.thumbBig.hashCode() : 0);
    }

    @org.jetbrains.annotations.NotNull
    public java.lang.String toString() {
        return "VideoEntity(title=" + this.title + ", description=" + this.description + ", thumbBig=" + this.thumbBig + ')';
    }

    public VideoEntity(@org.jetbrains.annotations.Nullable java.lang.String title, @org.jetbrains.annotations.Nullable java.lang.String description, @org.jetbrains.annotations.Nullable java.lang.String thumbBig) {
        this.title = title;
        this.description = description;
        this.thumbBig = thumbBig;
    }

    public /* synthetic */ VideoEntity(java.lang.String str, java.lang.String str2, java.lang.String str3, int i, kotlin.jvm.internal.DefaultConstructorMarker defaultConstructorMarker) {
        this((i & 1) != 0 ? null : str, (i & 2) != 0 ? null : str2, (i & 4) != 0 ? null : str3);
    }

    @org.jetbrains.annotations.Nullable
    public final java.lang.String getTitle() {
        return this.title;
    }

    @org.jetbrains.annotations.Nullable
    public final java.lang.String getDescription() {
        return this.description;
    }

    @org.jetbrains.annotations.Nullable
    public final java.lang.String getThumbBig() {
        return this.thumbBig;
    }
}
